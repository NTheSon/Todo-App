import json
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk

# Nếu chạy file .exe, lưu tasks.json cạnh file .exe thay vì trong
# thư mục tạm mà PyInstaller dùng khi khởi động chế độ --onefile.
APP_PATH = Path(sys.executable if getattr(sys, "frozen", False) else __file__).resolve()
DATA_FILE = APP_PATH.with_name("tasks.json")


def load_tasks():
    """Đọc dữ liệu JSON cũ; chưa có file thì bắt đầu bằng danh sách rỗng."""
    if not DATA_FILE.exists():
        return []

    with DATA_FILE.open("r", encoding="utf-8") as file:
        tasks = json.load(file)

    if not isinstance(tasks, list):
        raise ValueError("File tasks.json phải chứa một danh sách.")

    for task in tasks:
        if (not isinstance(task, dict)
                or not isinstance(task.get("title"), str)
                or not isinstance(task.get("done"), bool)):
            raise ValueError("Một công việc trong tasks.json không đúng định dạng.")

    return tasks


class TodoApp:
    def __init__(self, root, tasks):
        self.root = root
        self.tasks = tasks

        root.title("To-Do List - Python Tkinter")
        root.geometry("580x440")
        root.minsize(460, 340)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        main = ttk.Frame(root, padding=16)
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(2, weight=1)

        ttk.Label(main, text="DANH SÁCH CÔNG VIỆC",
                  font=("Arial", 17, "bold")).grid(
                      row=0, column=0, columnspan=3,
                      sticky="w", pady=(0, 12))

        self.task_entry = ttk.Entry(main)
        self.task_entry.grid(row=1, column=0, columnspan=2,
                             sticky="ew", padx=(0, 8))
        ttk.Button(main, text="Thêm", command=self.add_task).grid(
            row=1, column=2)
        self.task_entry.bind("<Return>", lambda event: self.add_task())

        list_frame = ttk.Frame(main)
        list_frame.grid(row=2, column=0, columnspan=3,
                        sticky="nsew", pady=(12, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self.task_list = tk.Listbox(
            list_frame, font=("Arial", 11), height=12,
            selectmode=tk.SINGLE, activestyle="none"
        )
        self.task_list.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical",
                                  command=self.task_list.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.task_list.configure(yscrollcommand=scrollbar.set)
        self.task_list.bind("<Double-Button-1>",
                            lambda event: self.toggle_task())

        buttons = ttk.Frame(main)
        buttons.grid(row=3, column=0, columnspan=3,
                     sticky="w", pady=(0, 10))
        ttk.Button(buttons, text="Đổi trạng thái",
                   command=self.toggle_task).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Sửa",
                   command=self.edit_task).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Xóa",
                   command=self.delete_task).pack(side="left")

        self.stats_label = ttk.Label(main, text="")
        self.stats_label.grid(row=4, column=0, columnspan=3,
                              sticky="w")
        self.refresh_list()
        self.task_entry.focus_set()

    def save_tasks(self):
        try:
            with DATA_FILE.open("w", encoding="utf-8") as file:
                json.dump(self.tasks, file, ensure_ascii=False, indent=4)
        except OSError as error:
            messagebox.showerror(
                "Không thể lưu dữ liệu",
                f"Thay đổi hiện chỉ nằm trong bộ nhớ.\n{error}",
                parent=self.root
            )

    def refresh_list(self, selected_index=None):
        self.task_list.delete(0, tk.END)
        for number, task in enumerate(self.tasks, start=1):
            status = "✓" if task["done"] else "○"
            self.task_list.insert(
                tk.END, f"{number}. [{status}] {task['title']}"
            )

        finished = sum(task["done"] for task in self.tasks)
        self.stats_label.config(
            text=f"Đã hoàn thành: {finished}/{len(self.tasks)} công việc"
        )
        if selected_index is not None and 0 <= selected_index < len(self.tasks):
            self.task_list.selection_set(selected_index)
            self.task_list.see(selected_index)

    def get_selected_index(self):
        selection = self.task_list.curselection()
        if not selection:
            messagebox.showwarning(
                "Chưa chọn công việc",
                "Hãy chọn một công việc trong danh sách.",
                parent=self.root
            )
            return None
        return selection[0]

    def add_task(self):
        title = self.task_entry.get().strip()
        if not title:
            messagebox.showwarning(
                "Thiếu tên", "Vui lòng nhập tên công việc.", parent=self.root
            )
            return
        self.tasks.append({"title": title, "done": False})
        self.save_tasks()
        self.refresh_list(len(self.tasks) - 1)
        self.task_entry.delete(0, tk.END)
        self.task_entry.focus_set()

    def toggle_task(self):
        index = self.get_selected_index()
        if index is None:
            return
        self.tasks[index]["done"] = not self.tasks[index]["done"]
        self.save_tasks()
        self.refresh_list(index)

    def edit_task(self):
        index = self.get_selected_index()
        if index is None:
            return
        new_title = simpledialog.askstring(
            "Sửa công việc", "Tên mới:",
            initialvalue=self.tasks[index]["title"], parent=self.root
        )
        if new_title is None:
            return
        if not new_title.strip():
            messagebox.showwarning(
                "Tên không hợp lệ", "Tên công việc không được để trống.",
                parent=self.root
            )
            return
        self.tasks[index]["title"] = new_title.strip()
        self.save_tasks()
        self.refresh_list(index)

    def delete_task(self):
        index = self.get_selected_index()
        if index is None:
            return
        if not messagebox.askyesno(
            "Xác nhận xóa", f"Xóa '{self.tasks[index]['title']}'?",
            parent=self.root
        ):
            return
        self.tasks.pop(index)
        self.save_tasks()
        self.refresh_list()


def main():
    root = tk.Tk()
    try:
        tasks = load_tasks()
    except (OSError, ValueError, UnicodeError) as error:
        messagebox.showerror(
            "Không đọc được dữ liệu",
            "Không thể mở tasks.json. Hãy kiểm tra hoặc sao lưu file này.\n"
            f"Chương trình chưa thay đổi dữ liệu.\n\n{error}",
            parent=root
        )
        root.destroy()
        return

    TodoApp(root, tasks)
    root.mainloop()


if __name__ == "__main__":
    main()
