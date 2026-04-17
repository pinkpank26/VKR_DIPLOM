import json
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import requests


BASE_URL = "http://127.0.0.1:8000"
TIMEOUT = 120


class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.token = None

    def set_token(self, token: str | None):
        self.token = token.strip() if token else None

    def headers(self) -> dict:
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _request(self, method: str, path: str, **kwargs):
        url = f"{self.base_url}{path}"
        kwargs.setdefault("timeout", TIMEOUT)
        kwargs.setdefault("headers", self.headers())
        response = requests.request(method, url, **kwargs)
        content_type = response.headers.get("content-type", "")

        if not response.ok:
            try:
                data = response.json()
                detail = data.get("detail", data)
            except Exception:
                detail = response.text
            raise RuntimeError(f"{response.status_code}: {detail}")

        if "application/json" in content_type:
            return response.json()
        return response.text

    def register(self, email: str, password: str, role: str):
        return self._request(
            "POST",
            "/auth/register",
            json={"email": email, "password": password, "role": role},
        )

    def login(self, email: str, password: str):
        return self._request(
            "POST",
            "/auth/login",
            json={"email": email, "password": password},
        )

    def import_csv(self, file_path: str):
        with open(file_path, "rb") as f:
            files = {"file": (file_path.split("/")[-1], f, "text/csv")}
            return self._request("POST", "/contacts/import_csv", files=files)

    def import_excel(self, file_path: str):
        with open(file_path, "rb") as f:
            files = {
                "file": (
                    file_path.split("/")[-1],
                    f,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            }
            return self._request("POST", "/contacts/import_excel", files=files)

    def create_template(self, name: str, subject: str, body: str):
        return self._request(
            "POST",
            "/templates",
            json={"name": name, "subject": subject, "body": body},
        )

    def list_templates(self):
        return self._request("GET", "/templates")

    def create_campaign(self, name: str, description: str, template_id: int):
        return self._request(
            "POST",
            "/campaigns",
            json={"name": name, "description": description, "template_id": template_id},
        )

    def list_campaigns(self):
        return self._request("GET", "/campaigns")

    def prepare_campaign(self, campaign_id: int):
        return self._request("POST", f"/campaigns/{campaign_id}/prepare")

    def send_campaign(self, campaign_id: int):
        return self._request("POST", f"/campaigns/{campaign_id}/send")

    def campaign_report(self, campaign_id: int):
        return self._request("GET", f"/campaigns/{campaign_id}/report")

    def open_campaign_report_html_url(self, campaign_id: int) -> str:
        return f"{self.base_url}/campaigns/{campaign_id}/report/html"

    def healthcheck(self):
        url = f"{self.base_url}/docs"
        response = requests.get(url, timeout=10)
        if response.ok:
            return {"ok": True, "message": f"FastAPI доступен: {url}"}
        return {"ok": False, "message": f"Сервер ответил кодом {response.status_code}"}


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Клиент системы массовых рассылок")
        self.geometry("1180x760")
        self.minsize(1000, 680)

        self.api = ApiClient(BASE_URL)

        self.base_url_var = tk.StringVar(value=BASE_URL)
        self.email_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.role_var = tk.StringVar(value="Маркетолог")
        self.token_var = tk.StringVar()
        self.selected_file_var = tk.StringVar(value="Файл не выбран")
        self.status_var = tk.StringVar(value="Готово")

        self.template_name_var = tk.StringVar()
        self.template_subject_var = tk.StringVar()
        self.campaign_name_var = tk.StringVar()
        self.campaign_desc_var = tk.StringVar()
        self.selected_template_var = tk.StringVar()
        self.selected_campaign_var = tk.StringVar()

        self.templates_cache: list[dict] = []
        self.campaigns_cache: list[dict] = []

        self._build_ui()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self, padding=12)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(1, weight=1)

        ttk.Label(header, text="Адрес API:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Entry(header, textvariable=self.base_url_var).grid(row=0, column=1, sticky="ew")
        ttk.Button(header, text="Применить", command=self.apply_base_url).grid(row=0, column=2, padx=8)
        ttk.Button(header, text="Проверить API", command=self.check_api).grid(row=0, column=3)

        body = ttk.Frame(self, padding=(12, 0, 12, 12))
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=0)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        left = ttk.Frame(body)
        left.grid(row=0, column=0, sticky="nsw", padx=(0, 12))
        right = ttk.Frame(body)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)

        self._build_auth_panel(left)
        self._build_actions_panel(left)
        self._build_right_panel(right)

        footer = ttk.Frame(self, padding=(12, 0, 12, 12))
        footer.grid(row=2, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)
        ttk.Label(footer, textvariable=self.status_var).grid(row=0, column=0, sticky="w")

    def _build_auth_panel(self, parent):
        frame = ttk.LabelFrame(parent, text="Авторизация", padding=12)
        frame.pack(fill="x", pady=(0, 12))

        ttk.Label(frame, text="Email").grid(row=0, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.email_var, width=34).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        ttk.Label(frame, text="Пароль").grid(row=2, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.password_var, show="*", width=34).grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        ttk.Label(frame, text="Роль при регистрации").grid(row=4, column=0, sticky="w")
        ttk.Combobox(
            frame,
            textvariable=self.role_var,
            values=["Маркетолог", "Админ"],
            state="readonly",
            width=31,
        ).grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        ttk.Button(frame, text="Регистрация", command=self.register_user).grid(row=6, column=0, sticky="ew", padx=(0, 4))
        ttk.Button(frame, text="Войти", command=self.login_user).grid(row=6, column=1, sticky="ew", padx=(4, 0))

        ttk.Label(frame, text="JWT токен").grid(row=7, column=0, sticky="w", pady=(12, 0))
        ttk.Entry(frame, textvariable=self.token_var, width=34).grid(row=8, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        ttk.Button(frame, text="Применить токен", command=self.apply_token).grid(row=9, column=0, sticky="ew", padx=(0, 4))
        ttk.Button(frame, text="Очистить", command=self.clear_token).grid(row=9, column=1, sticky="ew", padx=(4, 0))

        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

    def _build_actions_panel(self, parent):
        frame = ttk.LabelFrame(parent, text="Быстрые действия", padding=12)
        frame.pack(fill="x")

        ttk.Button(frame, text="Выбрать CSV или Excel", command=self.select_file).pack(fill="x", pady=(0, 6))
        ttk.Label(frame, textvariable=self.selected_file_var, wraplength=280).pack(fill="x", pady=(0, 6))
        ttk.Button(frame, text="Импортировать контакты", command=self.import_contacts).pack(fill="x", pady=(0, 12))

        ttk.Button(frame, text="Обновить шаблоны", command=self.refresh_templates).pack(fill="x", pady=(0, 6))
        ttk.Button(frame, text="Обновить кампании", command=self.refresh_campaigns).pack(fill="x", pady=(0, 6))
        ttk.Button(frame, text="Показать отчёт по кампании", command=self.show_report_for_selected).pack(fill="x", pady=(0, 6))
        ttk.Button(frame, text="Открыть HTML-отчёт", command=self.open_report_html_for_selected).pack(fill="x", pady=(0, 6))
        ttk.Button(frame, text="Подготовить кампанию", command=self.prepare_selected_campaign).pack(fill="x", pady=(0, 6))
        ttk.Button(frame, text="Отправить кампанию", command=self.send_selected_campaign).pack(fill="x")

    def _build_right_panel(self, parent):
        notebook = ttk.Notebook(parent)
        notebook.grid(row=0, column=0, sticky="nsew")

        tab_templates = ttk.Frame(notebook, padding=12)
        tab_campaigns = ttk.Frame(notebook, padding=12)
        tab_log = ttk.Frame(notebook, padding=12)

        notebook.add(tab_templates, text="Шаблоны")
        notebook.add(tab_campaigns, text="Кампании")
        notebook.add(tab_log, text="Лог")

        self._build_templates_tab(tab_templates)
        self._build_campaigns_tab(tab_campaigns)
        self._build_log_tab(tab_log)

    def _build_templates_tab(self, parent):
        parent.columnconfigure(0, weight=1)

        ttk.Label(parent, text="Название шаблона").grid(row=0, column=0, sticky="w")
        ttk.Entry(parent, textvariable=self.template_name_var).grid(row=1, column=0, sticky="ew", pady=(0, 8))

        ttk.Label(parent, text="Тема письма").grid(row=2, column=0, sticky="w")
        ttk.Entry(parent, textvariable=self.template_subject_var).grid(row=3, column=0, sticky="ew", pady=(0, 8))

        ttk.Label(parent, text="Тело письма").grid(row=4, column=0, sticky="w")
        self.template_body_text = tk.Text(parent, height=14, wrap="word")
        self.template_body_text.grid(row=5, column=0, sticky="nsew", pady=(0, 8))

        buttons = ttk.Frame(parent)
        buttons.grid(row=6, column=0, sticky="ew")
        buttons.columnconfigure(0, weight=1)
        buttons.columnconfigure(1, weight=1)
        ttk.Button(buttons, text="Создать шаблон", command=self.create_template).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ttk.Button(buttons, text="Обновить список", command=self.refresh_templates).grid(row=0, column=1, sticky="ew", padx=(4, 0))

        ttk.Label(parent, text="Доступные шаблоны").grid(row=7, column=0, sticky="w", pady=(12, 4))
        self.templates_list = tk.Listbox(parent, height=8)
        self.templates_list.grid(row=8, column=0, sticky="nsew")
        self.templates_list.bind("<<ListboxSelect>>", self.on_template_selected)

        parent.rowconfigure(5, weight=1)
        parent.rowconfigure(8, weight=1)

    def _build_campaigns_tab(self, parent):
        parent.columnconfigure(0, weight=1)

        ttk.Label(parent, text="Название кампании").grid(row=0, column=0, sticky="w")
        ttk.Entry(parent, textvariable=self.campaign_name_var).grid(row=1, column=0, sticky="ew", pady=(0, 8))

        ttk.Label(parent, text="Описание").grid(row=2, column=0, sticky="w")
        ttk.Entry(parent, textvariable=self.campaign_desc_var).grid(row=3, column=0, sticky="ew", pady=(0, 8))

        ttk.Label(parent, text="Template ID для кампании").grid(row=4, column=0, sticky="w")
        self.template_id_combo = ttk.Combobox(parent, textvariable=self.selected_template_var, state="readonly")
        self.template_id_combo.grid(row=5, column=0, sticky="ew", pady=(0, 8))

        actions = ttk.Frame(parent)
        actions.grid(row=6, column=0, sticky="ew")
        actions.columnconfigure(0, weight=1)
        actions.columnconfigure(1, weight=1)
        ttk.Button(actions, text="Создать кампанию", command=self.create_campaign).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ttk.Button(actions, text="Обновить кампании", command=self.refresh_campaigns).grid(row=0, column=1, sticky="ew", padx=(4, 0))

        ttk.Label(parent, text="Список кампаний").grid(row=7, column=0, sticky="w", pady=(12, 4))
        self.campaigns_tree = ttk.Treeview(parent, columns=("id", "name", "status"), show="headings", height=12)
        self.campaigns_tree.heading("id", text="ID")
        self.campaigns_tree.heading("name", text="Название")
        self.campaigns_tree.heading("status", text="Статус")
        self.campaigns_tree.column("id", width=80, anchor="center")
        self.campaigns_tree.column("name", width=300)
        self.campaigns_tree.column("status", width=120, anchor="center")
        self.campaigns_tree.grid(row=8, column=0, sticky="nsew")
        self.campaigns_tree.bind("<<TreeviewSelect>>", self.on_campaign_selected)

        buttons = ttk.Frame(parent)
        buttons.grid(row=9, column=0, sticky="ew", pady=(8, 0))
        for i in range(3):
            buttons.columnconfigure(i, weight=1)
        ttk.Button(buttons, text="Подготовить", command=self.prepare_selected_campaign).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ttk.Button(buttons, text="Отправить", command=self.send_selected_campaign).grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Button(buttons, text="Отчёт", command=self.show_report_for_selected).grid(row=0, column=2, sticky="ew", padx=(4, 0))

        parent.rowconfigure(8, weight=1)

    def _build_log_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        self.log_text = tk.Text(parent, wrap="word")
        self.log_text.grid(row=0, column=0, sticky="nsew")
        self.log("Приложение запущено. Сначала проверь API, затем зарегистрируйся или войди.")

    def set_status(self, text: str):
        self.status_var.set(text)

    def log(self, text: str):
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")

    def run_action(self, title: str, func, success_message: str | None = None):
        def worker():
            self.after(0, lambda: self.set_status(f"Выполняется: {title}"))
            try:
                result = func()
                self.after(0, lambda: self._on_action_success(title, result, success_message))
            except Exception as e:
                self.after(0, lambda err=e: self._on_action_error(title, err))

        threading.Thread(target=worker, daemon=True).start()

    def _on_action_success(self, title: str, result, success_message: str | None):
        self.set_status(f"Готово: {title}")
        if success_message:
            messagebox.showinfo("Успех", success_message)
        if result is not None:
            pretty = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False, indent=2)
            self.log(f"[{title}]\n{pretty}\n")

    def _on_action_error(self, title: str, error: Exception):
        self.set_status(f"Ошибка: {title}")
        self.log(f"[{title}] Ошибка: {error}\n")
        messagebox.showerror("Ошибка", f"{title}\n\n{error}")

    def apply_base_url(self):
        self.api.base_url = self.base_url_var.get().strip().rstrip("/")
        self.set_status(f"Адрес API: {self.api.base_url}")
        self.log(f"Используется API: {self.api.base_url}")

    def apply_token(self):
        self.api.set_token(self.token_var.get())
        self.set_status("Токен применён")
        self.log("JWT токен применён.")

    def clear_token(self):
        self.token_var.set("")
        self.api.set_token(None)
        self.set_status("Токен очищен")
        self.log("JWT токен очищен.")

    def check_api(self):
        self.apply_base_url()
        self.run_action("Проверка API", self.api.healthcheck, "Сервер доступен")

    def register_user(self):
        email = self.email_var.get().strip()
        password = self.password_var.get().strip()
        role = self.role_var.get().strip()
        if not email or not password:
            messagebox.showwarning("Внимание", "Укажи email и пароль.")
            return
        self.run_action(
            "Регистрация",
            lambda: self.api.register(email, password, role),
            "Пользователь зарегистрирован",
        )

    def login_user(self):
        email = self.email_var.get().strip()
        password = self.password_var.get().strip()
        if not email or not password:
            messagebox.showwarning("Внимание", "Укажи email и пароль.")
            return

        def action():
            data = self.api.login(email, password)
            token = data.get("access_token", "")
            self.token_var.set(token)
            self.api.set_token(token)
            return data

        self.run_action("Вход", action, "Вход выполнен, токен сохранён")

    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="Выберите файл с контактами",
            filetypes=[
                ("Таблицы и CSV", "*.csv *.xlsx"),
                ("CSV files", "*.csv"),
                ("Excel files", "*.xlsx"),
                ("All files", "*.*"),
            ],
        )
        if file_path:
            self.selected_file_var.set(file_path)
            self.log(f"Выбран файл: {file_path}")

    def import_contacts(self):
        file_path = self.selected_file_var.get().strip()
        if not file_path or file_path == "Файл не выбран":
            messagebox.showwarning("Внимание", "Сначала выбери CSV- или Excel-файл.")
            return

        lower_path = file_path.lower()
        if lower_path.endswith(".csv"):
            self.run_action(
                "Импорт контактов из CSV",
                lambda: self.api.import_csv(file_path),
                "Контакты импортированы из CSV",
            )
        elif lower_path.endswith(".xlsx"):
            self.run_action(
                "Импорт контактов из Excel",
                lambda: self.api.import_excel(file_path),
                "Контакты импортированы из Excel",
            )
        else:
            messagebox.showwarning("Внимание", "Поддерживаются только файлы .csv и .xlsx")

    def create_template(self):
        name = self.template_name_var.get().strip()
        subject = self.template_subject_var.get().strip()
        body = self.template_body_text.get("1.0", "end").strip()
        if not name or not subject or not body:
            messagebox.showwarning("Внимание", "Заполни название, тему и текст шаблона.")
            return

        def action():
            template_id = self.api.create_template(name, subject, body)
            self.after(0, lambda: self.refresh_templates(silent=True))
            return {"template_id": template_id}

        self.run_action("Создание шаблона", action, "Шаблон создан")

    def refresh_templates(self, silent: bool = False):
        def apply_templates(templates):
            self.templates_cache = templates
            self.templates_list.delete(0, "end")
            values = []
            for item in templates:
                label = f"{item['id']} — {item['name']}"
                self.templates_list.insert("end", label)
                values.append(str(item["id"]))
            self.template_id_combo["values"] = values
            if values and not self.selected_template_var.get():
                self.selected_template_var.set(values[0])

        def action():
            templates = self.api.list_templates()
            self.after(0, lambda data=templates: apply_templates(data))
            return templates

        if silent:
            try:
                templates = self.api.list_templates()
                apply_templates(templates)
            except Exception:
                pass
        else:
            self.run_action("Обновление шаблонов", action)

    def on_template_selected(self, _event=None):
        selection = self.templates_list.curselection()
        if not selection:
            return
        idx = selection[0]
        item = self.templates_cache[idx]
        self.selected_template_var.set(str(item["id"]))
        self.log(f"Выбран template_id={item['id']}")

    def create_campaign(self):
        name = self.campaign_name_var.get().strip()
        description = self.campaign_desc_var.get().strip()
        template_id = self.selected_template_var.get().strip()
        if not name or not template_id:
            messagebox.showwarning("Внимание", "Укажи название кампании и выбери шаблон.")
            return

        def action():
            campaign_id = self.api.create_campaign(name, description, int(template_id))
            self.after(0, lambda: self.refresh_campaigns(silent=True))
            return {"campaign_id": campaign_id}

        self.run_action("Создание кампании", action, "Кампания создана")

    def refresh_campaigns(self, silent: bool = False):
        def apply_campaigns(campaigns):
            self.campaigns_cache = campaigns
            for item in self.campaigns_tree.get_children():
                self.campaigns_tree.delete(item)
            for row in campaigns:
                self.campaigns_tree.insert("", "end", values=(row["id"], row["name"], row["status"]))

        def action():
            campaigns = self.api.list_campaigns()
            self.after(0, lambda data=campaigns: apply_campaigns(data))
            return campaigns

        if silent:
            try:
                campaigns = self.api.list_campaigns()
                apply_campaigns(campaigns)
            except Exception:
                pass
        else:
            self.run_action("Обновление кампаний", action)

    def get_selected_campaign_id(self) -> int | None:
        selection = self.campaigns_tree.selection()
        if not selection:
            return None
        values = self.campaigns_tree.item(selection[0], "values")
        if not values:
            return None
        return int(values[0])

    def on_campaign_selected(self, _event=None):
        campaign_id = self.get_selected_campaign_id()
        if campaign_id is not None:
            self.selected_campaign_var.set(str(campaign_id))
            self.log(f"Выбрана кампания campaign_id={campaign_id}")

    def prepare_selected_campaign(self):
        campaign_id = self.get_selected_campaign_id()
        if campaign_id is None:
            messagebox.showwarning("Внимание", "Сначала выбери кампанию в списке.")
            return

        def action():
            result = self.api.prepare_campaign(campaign_id)
            self.after(0, lambda: self.refresh_campaigns(silent=True))
            return result

        self.run_action("Подготовка кампании", action, "Сообщения подготовлены")

    def send_selected_campaign(self):
        campaign_id = self.get_selected_campaign_id()
        if campaign_id is None:
            messagebox.showwarning("Внимание", "Сначала выбери кампанию в списке.")
            return

        def action():
            result = self.api.send_campaign(campaign_id)
            self.after(0, lambda: self.refresh_campaigns(silent=True))
            return result

        self.run_action("Отправка кампании", action, "Отправка завершена")

    def show_report_for_selected(self):
        campaign_id = self.get_selected_campaign_id()
        if campaign_id is None:
            messagebox.showwarning("Внимание", "Сначала выбери кампанию в списке.")
            return
        self.run_action("Отчёт по кампании", lambda: self.api.campaign_report(campaign_id))

    def open_report_html_for_selected(self):
        campaign_id = self.get_selected_campaign_id()
        if campaign_id is None:
            messagebox.showwarning("Внимание", "Сначала выбери кампанию в списке.")
            return

        url = self.api.open_campaign_report_html_url(campaign_id)
        webbrowser.open(url)
        self.log(f"Открыт HTML-отчёт: {url}")


if __name__ == "__main__":
    app = App()
    app.mainloop()