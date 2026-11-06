"""Build helper: applies explicitly selected patches, builds and deploys locally."""
from pathlib import Path
import datetime
import hashlib
import locale
import os
import shutil
import subprocess
import tempfile

class BuildError(Exception):
    pass

class Engine:
    def __init__(self, root, emit=print, runner=None):
        self.root = Path(root).resolve()
        self.repo = self.root / 'simply-source'
        self.build_dir = self.root / 'app-build'
        self.dev = self.root / 'dev'
        self.target = self.root / 'test-build'
        self.emit = emit
        self.runner = runner or self._run
        self.built = False
        self.built_fingerprint = None
        self.logfile = self.root / 'assistant-build.log'

    def _run(self, args, env=None, label='', capture=False):
        self.emit('\n▶ ' + label)
        self.emit('Команда: ' + subprocess.list2cmdline([str(a) for a in args]))
        try:
            p = subprocess.Popen([str(a) for a in args], cwd=self.repo,
                env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL, encoding=locale.getpreferredencoding(False),
                errors='replace', bufsize=1, shell=False,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        except OSError as e:
            raise BuildError('Не удалось запустить инструмент: ' + str(e)) from e
        lines = []
        with self.logfile.open('a', encoding='utf-8') as log:
            log.write('\n=== ' + label + ' ===\n')
            for line in p.stdout:
                log.write(line)
                self.emit(line.rstrip('\r\n'))
                if capture:
                    lines.append(line.rstrip('\r\n'))
        rc = p.wait()
        if rc != 0:
            raise BuildError(f'{label}: код завершения {rc}. Подробности в журнале.')
        return lines

    def preflight(self):
        required = [self.repo / 'GmProject' / 'Mine-imator.yyp',
                    self.repo / 'CppProject' / 'CMakeLists.txt',
                    self.repo / 'CppGen' / 'CppGen' / 'CppGen.csproj',
                    self.repo / 'CppGen' / 'gml.json',
                    self.dev / 'Qt' / '5.15.9' / 'build' / 'lib' / 'cmake' / 'Qt5' / 'Qt5Config.cmake']
        missing = [str(p) for p in required if not p.is_file()]
        if missing:
            raise BuildError('Не найдены нужные файлы:\n' + '\n'.join(missing))
        for tool in ('git', 'dotnet', 'cmake'):
            if not shutil.which(tool):
                raise BuildError(f'Не найден {tool} в PATH. Установите его и перезапустите помощник.')

    def patch_check(self, patch):
        patch = Path(patch).resolve()
        if not (self.repo / '.git').exists():
            raise BuildError('В simply-source не найден Git-репозиторий.')
        if not patch.is_file() or patch.suffix.lower() != '.patch':
            raise BuildError('Выберите существующий файл .patch.')
        self.runner(['git', 'apply', '--check', str(patch)], label='Проверка патча')
        self.emit('Проверка пройдена. Изменения ещё не внесены.')

    def patch_apply(self, patch):
        self.built = False
        self.patch_check(patch)
        self.runner(['git', 'apply', str(Path(patch).resolve())], label='Применение патча')
        self.emit('Патч применён. Теперь нажмите «Собрать».')

    def source_fingerprint(self):
        # Detect source changes between generation, build and deployment.
        digest = hashlib.sha256()
        for name in ('GmProject', 'CppProject', 'CppGen'):
            root = self.repo / name
            for base, dirs, files in os.walk(root):
                dirs[:] = sorted(d for d in dirs if d not in ('.git', 'Generated', 'Asset', 'External', 'bin', 'obj', '.vs'))
                for name in sorted(files):
                    path = Path(base) / name
                    digest.update(str(path.relative_to(self.repo)).encode('utf-8'))
                    with path.open('rb') as f:
                        for block in iter(lambda: f.read(1024 * 1024), b''):
                            digest.update(block)
        return digest.digest()

    def compile(self):
        self.built = False
        self.preflight()
        before_build = self.source_fingerprint()
        project = self.repo / 'CppGen' / 'CppGen'
        with tempfile.TemporaryDirectory(prefix='mineimator-generator-') as tmp:
            local = Path(tmp) / 'CppGen'
            shutil.copytree(project, local, ignore=shutil.ignore_patterns('bin', 'obj', '.vs'))
            program = local / 'Program.cs'
            source = program.read_text(encoding='utf-8-sig')
            if source.count('Console.ReadLine()') != 1 or source.count('Console.ReadKey();') != 1:
                raise BuildError('Неожиданная версия CppGen: автоматизация остановлена, исходный генератор не изменён.')
            # Change only the disposable copy. Never overwrite shaders in GameMaker.
            source = source.replace('Console.ReadLine()', '"n"', 1).replace('Console.ReadKey();', '', 1)
            program.write_text(source, encoding='utf-8-sig')
            args = ['dotnet', 'run', '--project', str(local / 'CppGen.csproj'), '--',
                    str(self.repo / 'GmProject'), str(self.repo / 'CppProject' / 'Generated'),
                    str(self.repo / 'CppProject' / 'Asset' / 'Sprites'),
                    str(self.repo / 'CppProject' / 'Asset' / 'Shaders'), str(self.repo / 'CppGen' / 'gml.json')]
            output = self.runner(args, label='1/3 Преобразование GML в C++', capture=True)
            if not any(line.strip() == 'Success!' for line in output) or any('Finished with ' in line and ' errors' in line for line in output):
                raise BuildError('Генератор не подтвердил успешное завершение. Смотрите журнал.')
        env = os.environ.copy()
        env['DEV_DIR'] = str(self.dev)
        self.runner(['cmake', '-S', str(self.repo / 'CppProject'), '-B', str(self.build_dir),
                     '-G', 'Visual Studio 17 2022', '-A', 'x64'], env=env, label='2/3 Настройка CMake')
        self.runner(['cmake', '--build', str(self.build_dir), '--config', 'Release', '--parallel', '4'],
                    env=env, label='3/3 Сборка Release')
        exe = self.build_dir / 'Release' / 'Mine-imator.exe'
        if not exe.is_file():
            raise BuildError('Сборка завершилась, но Mine-imator.exe не найден.')
        after_build = self.source_fingerprint()
        if before_build != after_build:
            raise BuildError("Исходники изменились во время сборки. Соберите ещё раз, не меняя их.")
        self.built_fingerprint = after_build
        self.built = True
        self.emit('\nСборка готова. Старую тестовую версию пока не меняли.')

    def deploy(self):
        if not self.built:
            raise BuildError('Сначала успешно выполните «Собрать» в этом запуске помощника.')
        if self.source_fingerprint() != self.built_fingerprint:
            self.built = False
            raise BuildError('Исходники изменились после сборки. Соберите заново.')
        exe = self.build_dir / 'Release' / 'Mine-imator.exe'
        lang = self.repo / 'GmProject' / 'datafiles' / 'Data' / 'Languages' / 'english.milanguage'
        dest_exe = self.target / 'Mine-imator.exe'
        dest_lang = self.target / 'Data' / 'Languages' / 'english.milanguage'
        if not all(p.is_file() for p in (exe, lang, dest_exe, dest_lang)):
            raise BuildError('Не найдена программа или английский языковой файл в сборке либо тестовой папке. Ничего не заменено.')
        # Never overwrite a previous backup; backups are separate from app data.
        backup_root = self.root / 'assistant-backups'
        backup_root.mkdir(exist_ok=True)
        backup = Path(tempfile.mkdtemp(prefix=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-'), dir=backup_root))
        saved_exe, saved_lang = backup / 'Mine-imator.exe', backup / 'english.milanguage'
        shutil.copy2(dest_exe, saved_exe)
        shutil.copy2(dest_lang, saved_lang)
        self.emit('Резервная копия: ' + str(backup))
        try:
            shutil.copy2(exe, dest_exe)
            shutil.copy2(lang, dest_lang)
        except OSError as e:
            problems = []
            for src, dst in ((saved_exe, dest_exe), (saved_lang, dest_lang)):
                try:
                    shutil.copy2(src, dst)
                except OSError as restore_error:
                    problems.append(f'{dst}: {restore_error}')
            msg = 'Не удалось обновить тестовую версию: ' + str(e) + '\nКопия сохранена в ' + str(backup)
            if problems:
                msg += '\nНе удалось автоматически восстановить: ' + '; '.join(problems)
            else:
                msg += '\nПредыдущая версия восстановлена.'
            raise BuildError(msg) from e
        self.emit('Тестовая версия обновлена. Vexel и проекты не изменялись.')

    def launch(self):
        exe = self.target / 'Mine-imator.exe'
        if not exe.is_file():
            raise BuildError('В test-build не найден Mine-imator.exe.')
        subprocess.Popen([str(exe)], cwd=self.target, shell=False)
        self.emit('Тестовая версия запущена.')
