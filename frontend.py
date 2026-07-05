import streamlit as st
import json
import os
import random
from collections import Counter

#Конфигурация 
BOOKS_FILE = "books.json"
AUTHORS_FILE = "authors.json"
ISSUED_FILE = "issued.json"
CLIENTS_FILE = "clients.json"

#JSON
def load_json(filename, default=None):
    if default is None:
        default = [] if filename in (ISSUED_FILE, CLIENTS_FILE, BOOKS_FILE) else {}
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

#Хранилища
def load_books():
    return load_json(BOOKS_FILE, [])

def save_books(data):
    save_json(BOOKS_FILE, data)

def load_authors_details():
    return load_json(AUTHORS_FILE, {})

def save_authors_details(data):
    save_json(AUTHORS_FILE, data)

def load_issued():
    return load_json(ISSUED_FILE, [])

def save_issued(data):
    save_json(ISSUED_FILE, data)

def load_clients():
    return load_json(CLIENTS_FILE, [])

def save_clients(data):
    save_json(CLIENTS_FILE, data)

#работа с книгами
def add_or_update_book(author, title, year, genre, qty, image_url=""):
    books = load_books()
    full_title = f"{author} — {title}"
    if year:
        full_title += f" ({year})"
    for book in books:
        if book["full_title"] == full_title:
            book["quantity"] += qty
            save_books(books)
            return True, "Количество обновлено"
    new_book = {
        "full_title": full_title,
        "author": author,
        "title": title,
        "year": year,
        "genre": genre,
        "pages": 0,
        "image_url": image_url,
        "quantity": qty
    }
    books.append(new_book)
    save_books(books)
    return True, "Книга добавлена"

def decrease_book_quantity(full_title, qty):
    books = load_books()
    for book in books:
        if book["full_title"] == full_title:
            book["quantity"] = max(0, book["quantity"] - qty)
            save_books(books)
            return True
    return False

def increase_book_quantity(full_title, qty):
    books = load_books()
    for book in books:
        if book["full_title"] == full_title:
            book["quantity"] += qty
            save_books(books)
            return True
    return False

def update_book_record(old_full, new_full, updated_data):
    books = load_books()
    for i, book in enumerate(books):
        if book["full_title"] == old_full:
            books[i] = {**updated_data, "full_title": new_full}
            save_books(books)
            if old_full != new_full:
                issued = load_issued()
                for issue in issued:
                    if issue["book_title"] == old_full:
                        issue["book_title"] = new_full
                save_issued(issued)
            return True
    return False

#выдача
def add_client(name, phone):
    clients = load_clients()
    for c in clients:
        if c["name"].lower() == name.lower() and c["phone"] == phone:
            return c
    new_client = {"name": name, "phone": phone}
    clients.append(new_client)
    save_clients(clients)
    return new_client

def issue_book(book_title, client_name, client_phone, qty):
    add_client(client_name, client_phone)
    if not decrease_book_quantity(book_title, qty):
        return False
    issued = load_issued()
    issue_id = len(issued) + 1
    new_issue = {
        "id": issue_id,
        "book_title": book_title,
        "client_name": client_name,
        "client_phone": client_phone,
        "quantity": qty,
        "returned": False
    }
    issued.append(new_issue)
    save_issued(issued)
    return True

def return_book(issue_id):
    issued = load_issued()
    for issue in issued:
        if issue["id"] == issue_id and not issue["returned"]:
            issue["returned"] = True
            increase_book_quantity(issue["book_title"], issue["quantity"])
            save_issued(issued)
            return True
    return False

#пр
def get_unique_authors(books):
    authors = set()
    for book in books:
        if book["author"]:
            authors.add(book["author"])
    ad = load_authors_details()
    for a in ad:
        authors.add(a)
    return sorted(list(authors))

def get_author_details(author_name):
    ad = load_authors_details()
    if author_name not in ad:
        ad[author_name] = {"birth_date": "", "death_date": "", "alive": False, "photo_url": ""}
        save_authors_details(ad)
    return ad[author_name]

def get_all_genres(books):
    genres = set()
    for book in books:
        if book.get("genre") and book["genre"].strip():
            genres.add(book["genre"].strip())
    return sorted(list(genres))

def format_author_dates(details):
    birth = details.get("birth_date", "")
    if not birth:
        return "—"
    if details.get("alive", False):
        return f"{birth} – наши дни"
    death = details.get("death_date", "")
    if death:
        return f"{birth} – {death}"
    return birth

def book_cover_html(book, width=80):
    """HTML-обложка с рамкой и пропорциями 2:3."""
    aspect_ratio = 2/3
    height = int(width / aspect_ratio)
    if book.get("image_url"):
        img_tag = f'<img src="{book["image_url"]}" style="width:100%;height:100%;object-fit:cover;">'
    else:
        img_tag = f'<div style="width:100%;height:100%;background:#e0d8cc;display:flex;align-items:center;justify-content:center;font-size:2rem;color:#8b7355;">📖</div>'
    return f'<div style="width:{width}px;height:{height}px;border:1px solid #bcaaa4;border-radius:4px;overflow:hidden;flex-shrink:0;">{img_tag}</div>'

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None
if "page" not in st.session_state:
    st.session_state.page = "Главная" if st.session_state.username != "admin" else "Управление хранилищем"
if "edit_book" not in st.session_state:
    st.session_state.edit_book = None
if "edit_author" not in st.session_state:
    st.session_state.edit_author = None
if "selected_client" not in st.session_state:
    st.session_state.selected_client = None
if "selected_genre" not in st.session_state:
    st.session_state.selected_genre = None

st.set_page_config(page_title="Библиотека", layout="wide")

#стили
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&display=swap');

.stApp {
    background-color: #f5f0e6;
}
html, body, .stMarkdown, .stText, .stTitle, .stHeader, .stSubheader,
.stCaption, .stRadio label, .stButton button, .stTextInput label,
.stNumberInput label, .stSelectbox label, .stTextArea label {
    font-family: 'Cormorant Garamond', serif !important;
    color: #5c4033 !important;
}
h1, h2, h3, h4 {
    font-family: 'Cormorant Garamond', serif !important;
    color: #4a3728 !important;
    font-weight: 600;
}

.stButton > button {
    background-color: #d2b48c;
    color: #4a3728 !important;
    border: 1px solid #a0522d;
    font-weight: 600;
    border-radius: 12px;
    padding: 0.5rem 1rem;
    transition: background-color 0.3s ease;
}
.stButton > button:hover {
    background-color: #b8956a;
    color: #3e2723 !important;
}

.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background-color: #faf7f2;
    color: #5c4033;
    border: 1px solid #bcaaa4;
    border-radius: 10px;
}
.stTextInput > div > div:focus-within,
.stTextArea > div > div:focus-within {
    box-shadow: 0 0 0 1px #a0522d !important;
    border-color: #a0522d !important;
}

.stSelectbox div[data-baseweb="select"] > div {
    background-image: none !important;
}
.stSelectbox div[data-baseweb="select"]:focus-within {
    box-shadow: 0 0 0 1px #a0522d !important;
    border-color: #a0522d !important;
}
.stSelectbox div[data-baseweb="select"] > div > div > div {
    background-image: none !important;
}

/*Боковая панель*/
[data-testid="stSidebar"] {
    background-color: #d2b48c;
    padding: 1rem;
}
[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    text-align: left;
    font-size: 1.3rem;
    font-weight: 600;
    background-color: transparent;
    border: none;
    border-radius: 0;
    margin-bottom: 2px;
    padding: 0.8rem 1rem;
    color: #4a3728 !important;
    transition: background-color 0.3s;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background-color: rgba(0,0,0,0.1);
}

/* Заголовок слева */
.merged-title {
    font-size: 2rem;
    font-weight: 700;
    color: #4a3728;
    margin: 1rem 0;
    text-align: left;
}
/*размеры*/
.detail-img {
    width: 200px;
    height: 300px;
    object-fit: cover;
    border: 1px solid #bcaaa4;
    border-radius: 4px;
}

/* Кнопка-ссылка на автора*/
.author-link-wrapper .stButton > button {
    background: none !important;
    border: none !important;
    color: #4a3728 !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
    padding: 0 !important;
    text-decoration: underline;
    font-family: 'Cormorant Garamond', serif !important;
    cursor: pointer;
}
.author-link-wrapper .stButton > button:hover {
    color: #a0522d !important;
}
</style>
""", unsafe_allow_html=True)

#вход
if not st.session_state.authenticated:
    st.title("🔐 Вход в систему")
    with st.form("login_form"):
        username = st.text_input("Логин")
        password = st.text_input("Пароль", type="password")
        if st.form_submit_button("Войти"):
            if username == "admin" and password == "admin":
                st.session_state.authenticated = True
                st.session_state.username = "admin"
                st.session_state.page = "Управление хранилищем"
                st.rerun()
            elif username == "user" and password == "user":
                st.session_state.authenticated = True
                st.session_state.username = "user"
                st.session_state.page = "Главная"
                st.rerun()
            else:
                st.error("Неверный логин или пароль")
    st.stop()

#Боковая панель
with st.sidebar:
    st.title("📚 Меню")
    if st.session_state.username == "admin":
        pages = ["Управление хранилищем", "Список книг", "Список авторов",
                 "Жанры", "Выданные книги", "Клиенты", "Выход"]
    else:
        pages = ["Главная", "Список книг", "Список авторов", "Жанры", "Выход"]

    for page in pages:
        if st.button(page, key=f"nav_{page}", use_container_width=True):
            if page == st.session_state.page:
                if page == "Список авторов" and st.session_state.edit_author:
                    st.session_state.edit_author = None
                elif page == "Список книг" and st.session_state.edit_book:
                    st.session_state.edit_book = None
                elif page == "Жанры" and st.session_state.selected_genre:
                    st.session_state.selected_genre = None
                elif page == "Клиенты" and st.session_state.selected_client:
                    st.session_state.selected_client = None
                st.rerun()
            else:
                st.session_state.page = page
                st.session_state.edit_book = None
                st.session_state.edit_author = None
                st.session_state.selected_client = None
                st.session_state.selected_genre = None
                if "show_issue" in st.session_state:
                    del st.session_state.show_issue
                st.rerun()

if st.session_state.page == "Выход":
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.page = "Главная"
    st.rerun()

books = load_books()
is_admin = (st.session_state.username == "admin")

#отображение списка книг
def show_book_list(book_list, show_quantity=True):
    for book in book_list:
        col_img, col_info = st.columns([1, 5])
        with col_img:
            st.markdown(book_cover_html(book, 100), unsafe_allow_html=True)
        with col_info:
            st.markdown(f"<div style='font-weight:700; font-size:1.2rem; line-height:1.3;'>{book['title']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:1rem; color:#4a3728;'>{book['author']}</div>", unsafe_allow_html=True)
            year_text = book.get('year', '—')
            if show_quantity and book["quantity"] == 0:
                year_text += " <span style='color:#c62828; font-weight:600;'>(нет в наличии)</span>"
            st.markdown(f"<div style='font-size:0.9rem; color:#6d4c41;'>{year_text}</div>", unsafe_allow_html=True)
            if st.button("Подробнее", key=f"book_{book['full_title']}"):
                st.session_state.edit_book = book["full_title"]
                st.session_state.page = "Список книг"
                st.rerun()
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

#Главная
if st.session_state.page == "Главная":
    st.title("📚 Добро пожаловать в библиотеку!")
    if books:
        st.subheader("✨ Рекомендация дня")
        random_book = random.choice(books)
        book_img = random_book.get("image_url")
        author_det = get_author_details(random_book["author"])
        author_img = author_det.get("photo_url")
        cols = st.columns(2)
        with cols[0]:
            if book_img:
                st.image(book_img, width=200, output_format="auto")
            else:
                st.markdown(book_cover_html(random_book, 200), unsafe_allow_html=True)
        with cols[1]:
            if author_img:
                st.image(author_img, width=200, output_format="auto")
            else:
                st.markdown(book_cover_html({"image_url": None}, 200), unsafe_allow_html=True)
        st.markdown(f"<div class='merged-title'>{random_book['author']} — {random_book['title']}</div>",
                    unsafe_allow_html=True)
        if st.button(f"👤 Об авторе: {random_book['author']}", key=f"main_auth_{random_book['author']}"):
            st.session_state.edit_author = random_book['author']
            st.session_state.page = "Список авторов"
            st.rerun()
        st.markdown(f"**Год:** {random_book.get('year', '—')}")
        st.markdown(f"**Жанр:** {random_book.get('genre', '—')}")
        st.markdown(f"**Страниц:** {random_book.get('pages', '—')}")
        if random_book["quantity"] > 0:
            st.markdown("**В наличии**")
        else:
            st.markdown("**Нет в наличии**")
        if st.button("📖 Перейти к книге"):
            st.session_state.edit_book = random_book["full_title"]
            st.session_state.page = "Список книг"
            st.rerun()
    else:
        st.info("Пока нет книг в библиотеке.")

    st.subheader("🏆 Топ популярных книг")
    issued = load_issued()
    if issued:
        book_counter = Counter()
        for issue in issued:
            book_counter[issue["book_title"]] += issue["quantity"]
        top_books = book_counter.most_common(5)
        if top_books:
            for idx, (title, count) in enumerate(top_books, 1):
                st.write(f"{idx}. **{title}**")
                book_data = next((b for b in books if b["full_title"] == title), None)
                if book_data:
                    show_book_list([book_data], show_quantity=False)
        else:
            st.write("Пока нет статистики выдач.")
    else:
        st.write("История выдач пуста.")

#хранилище
elif st.session_state.page == "Управление хранилищем":
    st.title("⚙️ Управление хранилищем")
    with st.form("warehouse_form", clear_on_submit=True):
        op = st.radio("Действие", ["Добавить", "Удалить"], horizontal=True)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            author = st.text_input("Автор")
        with col2:
            title = st.text_input("Название")
        with col3:
            year = st.text_input("Год")
        with col4:
            genre = st.text_input("Жанр")
        qty = st.number_input("Количество", 1, 9999, 1)
        if st.form_submit_button("Выполнить"):
            if not author.strip() or not title.strip():
                st.error("Автор и название обязательны!")
            else:
                if op == "Добавить":
                    success, msg = add_or_update_book(author.strip(), title.strip(), year.strip(), genre.strip(), qty)
                else:
                    full_title = f"{author.strip()} — {title.strip()}"
                    if year.strip():
                        full_title += f" ({year.strip()})"
                    success = decrease_book_quantity(full_title, qty)
                    msg = "Количество уменьшено" if success else "Книга не найдена"
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    st.subheader("📋 Текущие остатки")
    if books:
        search = st.text_input("🔍 Поиск по автору или названию", key="wh_search")
        filtered = [b for b in books if search.lower() in b["full_title"].lower()] if search else books
        if filtered:
            st.info(f"Позиций: {len(filtered)}, всего книг: {sum(b['quantity'] for b in filtered)}")
            show_book_list(filtered, show_quantity=True)
        else:
            st.warning("Ничего не найдено")
    else:
        st.warning("Склад пуст")

#список книг 
elif st.session_state.page == "Список книг":
    if st.session_state.edit_book is not None:
        full_old = st.session_state.edit_book
        book_data = next((b for b in books if b["full_title"] == full_old), None)
        if not book_data:
            st.error("Книга не найдена")
            st.session_state.edit_book = None
            st.rerun()
        current_qty = book_data["quantity"]

        st.title(f"📖 {book_data['title']}")

        book_img = book_data.get("image_url")
        author_det = get_author_details(book_data["author"])
        author_img = author_det.get("photo_url")

        cols = st.columns(2)
        with cols[0]:
            if book_img:
                st.image(book_img, width=200, output_format="auto")
            else:
                st.markdown(book_cover_html(book_data, 200), unsafe_allow_html=True)
        with cols[1]:
            if author_img:
                st.image(author_img, width=200, output_format="auto")
            else:
                st.markdown(book_cover_html({"image_url": None}, 200), unsafe_allow_html=True)

        st.markdown('<div class="author-link-wrapper">', unsafe_allow_html=True)
        if st.button(book_data["author"], key="author_link_from_book"):
            st.session_state.edit_author = book_data["author"]
            st.session_state.page = "Список авторов"
            st.session_state.edit_book = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown(f"**Год:** {book_data.get('year', '—')}")
        st.markdown(f"**Жанр:** {book_data.get('genre', '—')}")
        st.markdown(f"**Страниц:** {book_data.get('pages', '—')}")
        if current_qty > 0:
            st.markdown("**В наличии**")
        else:
            st.markdown("**Нет в наличии**")

        if is_admin:
            st.subheader("Редактирование")
            with st.form("edit_book_form", clear_on_submit=False):
                new_author = st.text_input("Автор", value=book_data["author"])
                new_title = st.text_input("Название", value=book_data["title"])
                new_year = st.text_input("Год", value=book_data.get("year", ""))
                new_pages = st.number_input("Страниц", 0, 99999, value=int(book_data.get("pages", 0)))
                new_genre = st.text_input("Жанр", value=book_data.get("genre", ""))
                new_image = st.text_input("URL изображения книги", value=book_data.get("image_url", ""))
                new_qty = st.number_input("Количество на складе", 0, 9999, value=current_qty)

                cols_btn = st.columns(4)
                with cols_btn[0]:
                    back_btn = st.form_submit_button("↩️ Назад к списку")
                with cols_btn[1]:
                    save_btn = st.form_submit_button("💾 Сохранить")
                with cols_btn[2]:
                    if current_qty > 0:
                        issue_btn = st.form_submit_button("📤 Выдать книгу")
                    else:
                        issue_btn = False

            if back_btn:
                st.session_state.edit_book = None
                if "show_issue" in st.session_state:
                    del st.session_state.show_issue
                st.rerun()
            if save_btn:
                if not new_author.strip() or not new_title.strip():
                    st.error("Автор и название не могут быть пустыми")
                else:
                    new_full = f"{new_author.strip()} — {new_title.strip()}"
                    if new_year.strip():
                        new_full += f" ({new_year.strip()})"
                    updated_data = {
                        "author": new_author.strip(),
                        "title": new_title.strip(),
                        "year": new_year.strip(),
                        "genre": new_genre.strip(),
                        "pages": new_pages,
                        "image_url": new_image.strip(),
                        "quantity": new_qty
                    }
                    if update_book_record(full_old, new_full, updated_data):
                        st.session_state.edit_book = None
                        if "show_issue" in st.session_state:
                            del st.session_state.show_issue
                        st.success("Книга обновлена")
                        st.rerun()
                    else:
                        st.error("Ошибка обновления")
            if issue_btn:
                st.session_state.show_issue = True
                st.rerun()

            if "show_issue" in st.session_state and st.session_state.show_issue:
                st.divider()
                st.subheader("📤 Выдача книги")
                available_books = [b for b in books if b["quantity"] > 0]
                if not available_books:
                    st.warning("Нет книг в наличии для выдачи.")
                else:
                    book_titles = [b["full_title"] for b in available_books]
                    default_index = book_titles.index(full_old) if full_old in book_titles else 0
                    selected_book = st.selectbox("Книга", book_titles, index=default_index, key="issue_book_select")
                    max_qty = next(b["quantity"] for b in available_books if b["full_title"] == selected_book)
                    clients = load_clients()
                    client_options = ["Новый клиент"] + [f"{c['name']} ({c['phone']})" for c in clients]
                    selected_option = st.selectbox("Клиент", client_options, key="issue_client")
                    if selected_option == "Новый клиент":
                        client_name = st.text_input("Имя клиента", key="new_client_name")
                        client_phone = st.text_input("Телефон", key="new_client_phone")
                    else:
                        idx = client_options.index(selected_option) - 1
                        client_name = clients[idx]["name"]
                        client_phone = clients[idx]["phone"]
                        st.write(f"Выбран: {client_name}, тел. {client_phone}")
                    issue_qty = st.number_input("Количество к выдаче", min_value=1, max_value=max_qty, value=1, key="issue_qty")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Подтвердить выдачу"):
                            if not client_name or not client_phone:
                                st.error("Заполните данные клиента")
                            else:
                                if issue_book(selected_book, client_name, client_phone, issue_qty):
                                    st.success(f"Книга выдана клиенту {client_name}")
                                    del st.session_state.show_issue
                                    st.session_state.edit_book = None
                                    st.rerun()
                                else:
                                    st.error("Ошибка выдачи")
                    with col2:
                        if st.button("Отмена", key="cancel_issue"):
                            del st.session_state.show_issue
                            st.rerun()
        else:
            if st.button("↩️ Назад к списку"):
                st.session_state.edit_book = None
                st.rerun()
    else:
        st.title("📖 Список книг")
        search = st.text_input("🔍 Поиск по автору или названию", key="books_search")
        filtered = [b for b in books if search.lower() in b["full_title"].lower()] if search else books
        if not filtered:
            st.info("Книги не найдены")
        else:
            show_book_list(filtered, show_quantity=is_admin)

#Список авторов
elif st.session_state.page == "Список авторов":
    st.title("👤 Авторы")
    authors_list = get_unique_authors(books)

    if st.session_state.edit_author is not None:
        author_name = st.session_state.edit_author
        details = get_author_details(author_name)

        col_photo, col_info = st.columns([1, 2])
        with col_photo:
            if details.get("photo_url"):
                st.image(details["photo_url"], width=200, output_format="auto")
            else:
                st.markdown(book_cover_html({"image_url": None}, 200), unsafe_allow_html=True)
        with col_info:
            st.subheader(f"{author_name}")
            st.markdown(f"**Годы жизни:** {format_author_dates(details)}")
            if is_admin:
                with st.expander("Редактировать"):
                    with st.form("author_form", clear_on_submit=False):
                        birth_date = st.text_input("Год рождения", value=details.get("birth_date", ""), key="birth")
                        alive = st.checkbox("По наши дни", value=details.get("alive", False))
                        death_date = ""
                        if not alive:
                            death_date = st.text_input("Год смерти", value=details.get("death_date", ""), key="death")
                        photo_url = st.text_input("URL фотографии", value=details.get("photo_url", ""))
                        if st.form_submit_button("💾 Сохранить"):
                            ad = load_authors_details()
                            ad[author_name] = {
                                "birth_date": birth_date.strip(),
                                "death_date": death_date.strip() if not alive else "",
                                "alive": alive,
                                "photo_url": photo_url.strip()
                            }
                            save_authors_details(ad)
                            st.success("Сохранено")
                            st.rerun()
            if st.button("↩️ Назад к списку авторов", key="back_from_author"):
                st.session_state.edit_author = None
                st.rerun()

        st.divider()
        st.write("**Книги этого автора:**")
        author_books = [b for b in books if b["author"].lower() == author_name.lower()]
        if author_books:
            show_book_list(author_books, show_quantity=is_admin)
        else:
            st.write("Нет книг в наличии")
    else:
        search_a = st.text_input("🔍 Поиск автора", key="auth_search")
        filtered_authors = [a for a in authors_list if search_a.lower() in a.lower()] if search_a else authors_list
        if not filtered_authors:
            st.info("Авторы не найдены")
        else:
            for a in filtered_authors:
                if st.button(a, key=f"auth_{a}", use_container_width=True):
                    st.session_state.edit_author = a
                    st.rerun()

#Жанры
elif st.session_state.page == "Жанры":
    st.title("🏷️ Жанры")
    genres = get_all_genres(books)

    if st.session_state.selected_genre is None:
        if not genres:
            st.info("Пока нет ни одного жанра.")
        else:
            for genre in genres:
                genre_books = [b for b in books if b.get("genre") == genre]
                total_qty = sum(b["quantity"] for b in genre_books)
                if st.button(f"{genre} ({len(genre_books)} книг, {total_qty} шт.)" if is_admin else f"{genre} ({len(genre_books)} книг)",
                             key=f"genre_{genre}"):
                    st.session_state.selected_genre = genre
                    st.rerun()
    else:
        genre = st.session_state.selected_genre
        st.subheader(f"Жанр: {genre}")
        genre_books = [b for b in books if b.get("genre") == genre]
        if genre_books:
            show_book_list(genre_books, show_quantity=is_admin)
        else:
            st.write("Нет книг этого жанра.")
        if st.button("↩️ Назад к списку жанров"):
            st.session_state.selected_genre = None
            st.rerun()

#Выданные книги
elif st.session_state.page == "Выданные книги":
    st.title("📤 Выданные книги")
    issued = load_issued()
    active = [i for i in issued if not i["returned"]]

    search_issued = st.text_input("🔍 Поиск по автору или названию", key="issued_search")
    if search_issued:
        active = [i for i in active if search_issued.lower() in i["book_title"].lower()]

    if not active:
        st.info("Нет выданных книг" if not search_issued else "Ничего не найдено")
    else:
        for issue in active:
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            with col1:
                st.write(f"**{issue['book_title']}**")
            with col2:
                if st.button(issue["client_name"], key=f"client_{issue['id']}"):
                    client = {"name": issue["client_name"], "phone": issue["client_phone"]}
                    st.session_state.selected_client = client
                    st.session_state.page = "Клиенты"
                    st.rerun()
            with col3:
                st.write(f"📞 {issue['client_phone']}")
            with col4:
                if st.button("↩️ Вернуть", key=f"ret_{issue['id']}"):
                    if return_book(issue["id"]):
                        st.success("Книга возвращена на склад")
                        st.rerun()
                    else:
                        st.error("Ошибка возврата")
            st.caption(f"Кол-во: {issue['quantity']}")
            st.divider()

#Клиенты
elif st.session_state.page == "Клиенты":
    st.title("👥 Клиенты")
    clients = load_clients()
    
    search_query = st.text_input("🔍 Поиск по имени или телефону", key="client_search")
    if search_query:
        filtered_clients = [c for c in clients if search_query.lower() in c["name"].lower() or search_query in c["phone"]]
    else:
        filtered_clients = clients

    if not filtered_clients:
        st.info("Клиенты не найдены" if search_query else "Пока нет клиентов")
    else:
        for c in filtered_clients:
            if st.button(f"{c['name']} — 📞 {c['phone']}", key=f"cli_{c['name']}_{c['phone']}"):
                st.session_state.selected_client = c
                st.rerun()

    if st.session_state.selected_client:
        client = st.session_state.selected_client
        st.subheader(f"История клиента: {client['name']} ({client['phone']})")
        issued = load_issued()
        client_issues = [i for i in issued if i["client_name"] == client["name"] and i["client_phone"] == client["phone"]]
        if client_issues:
            for issue in client_issues:
                status = "🟢 На руках" if not issue["returned"] else "🔴 Возвращена"
                st.write(f"- {issue['book_title']} | {issue['quantity']} шт. | {status}")
        else:
            st.write("История пуста")
        if st.button("↩️ Назад к списку клиентов"):
            st.session_state.selected_client = None
            st.rerun()