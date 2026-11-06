import queue
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from pathlib import Path
from engine import Engine

class App:
    def __init__(self, root):
        self.window = root
        self.path = Path(__file__).resolve().parent.parent
        self.events = queue.Queue()
        self.busy = False
        self.selected = tk.StringVar(value='Патч не выбран')
        self.status = tk.StringVar(value='Готово')
        self.engine = Engine(self.path, emit=lambda line: self.events.put(('log', line)))
        root.title('Помощник сборки Mine-imator')
        root.geometry('820x620')
        root.minsize(660, 500)
        root.protocol('WM_DELETE_WINDOW', self.close)
        frame = ttk.Frame(root, padding=14)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='Помощник сборки Mine-imator', font=('Segoe UI', 16, 'bold')).pack(anchor='w')
        ttk.Label(frame, text='Работает только с папками simply-source, app-build и test-build рядом с помощником.', wraplength=760).pack(anchor='w', pady=(4, 10))
        ttk.Label(frame, text='1. Выбери и примени файл патча (.patch)', font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        row = ttk.Frame(frame); row.pack(fill='x', pady=(4, 10))
        self.buttons = []
        self.button(row, 'Выбрать патч', self.choose).pack(side='left')
        self.button(row, 'Проверить', self.check).pack(side='left', padx=5)
        self.button(row, 'Применить', self.apply).pack(side='left')
        ttk.Label(frame, textvariable=self.selected, wraplength=760).pack(anchor='w', pady=(0, 10))
        ttk.Label(frame, text='2. Собери и обнови тестовую версию', font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        row2 = ttk.Frame(frame); row2.pack(fill='x', pady=(5, 9))
        self.button(row2, 'Собрать', self.build).pack(side='left')
        self.button(row2, 'Обновить test-build', self.deploy).pack(side='left', padx=5)
        self.button(row2, 'Запустить test-build', self.launch).pack(side='left')
        ttk.Label(frame, textvariable=self.status, foreground='#245c98').pack(anchor='w')
        self.text = scrolledtext.ScrolledText(frame, height=15, wrap='word', state='disabled', font=('Consolas', 9))
        self.text.pack(fill='both', expand=True, pady=(7, 4))
        ttk.Label(frame, text='Полный журнал: assistant-build.log. Сборка может занять несколько минут.', wraplength=760).pack(anchor='w')
        root.after(120, self.pump)

    def button(self, parent, label, command):
        b = ttk.Button(parent, text=label, command=command)
        self.buttons.append(b)
        return b

    def choose(self):
        p = filedialog.askopenfilename(title='Выберите распакованный файл патча', initialdir=str(self.path),
                                       filetypes=[('Файлы патча', '*.patch'), ('Все файлы', '*.*')])
        if p: self.selected.set(p)

    def patch(self):
        p = Path(self.selected.get())
        if not p.is_file() or p.suffix.lower() != '.patch':
            messagebox.showwarning('Нужен патч', 'Сначала выберите распакованный файл .patch.')
            return None
        return p

    def check(self):
        p = self.patch()
        if p: self.work('Проверка патча', lambda: self.engine.patch_check(p))

    def apply(self):
        p = self.patch()
        if p and messagebox.askyesno('Применить патч?', f'Будут изменены исходники simply-source.\n\nПатч: {p.name}\n\nПрименить?'):
            self.work('Применение патча', lambda: self.engine.patch_apply(p))

    def build(self):
        if messagebox.askyesno('Собрать?', 'Сначала будет запущен генератор C++, затем CMake и сборка Release.\nТестовая версия пока не изменится. Продолжить?'):
            self.work('Сборка — подождите', self.engine.compile)

    def deploy(self):
        if not self.engine.built:
            messagebox.showwarning('Сначала сборка', 'Сначала успешно нажмите «Собрать» в этом запуске помощника.')
            return
        if messagebox.askyesno('Обновить тестовую версию?', 'Закройте Mine-imator перед обновлением.\n\nБудут заменены Mine-imator.exe и английский языковой файл в test-build. Сначала помощник сохранит их резервную копию. Продолжить?'):
            self.work('Обновление test-build', self.engine.deploy)

    def launch(self):
        self.work('Запуск test-build', self.engine.launch)

    def work(self, title, func):
        if self.busy: return
        self.busy = True
        self.status.set(title)
        for b in self.buttons: b.state(['disabled'])
        def run():
            try:
                func()
                self.events.put(('done', title))
            except Exception as exc:
                self.events.put(('error', str(exc)))
        threading.Thread(target=run, daemon=True).start()

    def append(self, line):
        self.text.configure(state='normal')
        self.text.insert('end', line + '\n')
        # Keep the GUI responsive; the complete tool output remains in the log.
        if int(self.text.index('end-1c').split('.')[0]) > 4000:
            self.text.delete('1.0', '1001.0')
        self.text.see('end')
        self.text.configure(state='disabled')

    def pump(self):
        for _ in range(150):
            try: kind, value = self.events.get_nowait()
            except queue.Empty: break
            if kind == 'log': self.append(value)
            elif kind in ('done', 'error'):
                self.busy = False
                for b in self.buttons: b.state(['!disabled'])
                if kind == 'error':
                    self.status.set('Ошибка')
                    self.append('\nОШИБКА: ' + value)
                    messagebox.showerror('Не удалось выполнить', value)
                else: self.status.set(value + ': готово')
        self.window.after(120, self.pump)

    def close(self):
        if self.busy:
            messagebox.showinfo('Операция выполняется', 'Дождитесь завершения операции, затем закройте окно.')
        else: self.window.destroy()

if __name__ == '__main__':
    if sys.platform != 'win32':
        print('Эта версия помощника предназначена для Windows.')
        sys.exit(1)
    app = tk.Tk()
    App(app)
    app.mainloop()
