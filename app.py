import streamlit as st
import time
from logic.generator import generate_validated_task
from logic.evaluator import run_python_code

TOPICS = {
    "Backend (Python)": [
        "🐍 Манипуляции со строками", 
        "📊 Списки и фильтрация",
        "🔐 Валидация паролей и логика",
        "📦 Идемпотентность и обработка транзакций",
        "🌐 Парсинг API-ответов"
    ],
    "Frontend (JS/React)": [
        "✨ Шаблонные строки и работа с DOM",
        "🗂️ Рендеринг списков через .map()",
        "🔘 Состояние кнопок и счетчиков (useState)",
        "📝 Управляемые формы (ввод текста)",
        "⏳ Индикатор загрузки данных (useEffect)"
    ]
}

st.set_page_config(page_title="DuoCoding AI", layout="wide")

# Состояние
if "task" not in st.session_state: st.session_state.task = None
if "attempts" not in st.session_state: st.session_state.attempts = 0
if "user_code" not in st.session_state: st.session_state.user_code = ""
if "run_results" not in st.session_state: st.session_state.run_results = None
if "celebrated" not in st.session_state: st.session_state.celebrated = False

# --- САЙДБАР ---
with st.sidebar:
    st.header("⚙️ Настройки")
    selected_track = st.selectbox("Трек", list(TOPICS.keys()))
    selected_topic = st.selectbox("Тема", TOPICS[selected_track])
    selected_level = st.selectbox("Уровень", ["Beginner", "Intermediate", "Advanced"])
    generate_clicked = st.button("🚀 Сгенерировать", type="primary", use_container_width=True)

    if st.session_state.task:
        st.divider()
        st.header("💡 Подсказки")
        for i, hint in enumerate(st.session_state.task.hints, 1):
            with st.expander(f"Подсказка {i}"):
                st.write(hint)

# --- ОСНОВНОЙ ЭКРАН ---
if generate_clicked:
    with st.status("🛠 Создаем задачу...", expanded=True) as status:
        st.write("📡 Подключаемся к ИИ-наставнику...")
        time.sleep(0.5)
        
        st.write("🧠 Придумываем интересный сюжет...")
        new_task = generate_validated_task(selected_track, selected_topic, selected_level)
        
        if new_task:
            st.write("🧪 Проверяем решение и тесты...")
            time.sleep(0.5)
            st.write("✨ Оформляем условие...")
            
            st.session_state.task = new_task
            st.session_state.attempts = 0
            st.session_state.run_results = None
            st.session_state.user_code = new_task.starter_code
            st.session_state.celebrated = False
            
            status.update(label="Задание готово! 🎯", state="complete", expanded=False)
            time.sleep(0.5)
            st.rerun()
        else:
            status.update(label="Упс! Что-то пошло не так", state="error", expanded=True)
            st.error("ИИ задумался слишком сильно. Попробуйте еще раз.")

task = st.session_state.task

if not task:
    st.title("Добро пожаловать в DuoCoding! 👋")
    st.info("Выбери тему слева и нажми 'Сгенерировать'.")
else:
    st.title(f"📝 {task.title}")
    st.markdown(task.description)
    
    user_code_input = st.text_area("Твой код:", value=st.session_state.user_code, height=250)

    col_btn, col_stats = st.columns([1, 3])
    with col_btn:
        if st.button("▶️ Запустить код"):
            st.session_state.user_code = user_code_input
            st.session_state.attempts += 1
            
            if "Backend" in selected_track:
                res = run_python_code(user_code_input, task.test_cases)
                st.session_state.run_results = res
                if res["status"] == "success" and res["passed"] == res["total"] and not st.session_state.celebrated:
                    st.balloons()
                    st.session_state.celebrated = True
            else:
                st.session_state.run_results = {"status": "info", "message": "JS-тесты недоступны в MVP"}

    with col_stats:
        st.write(f"**Попыток использовано:** {st.session_state.attempts} / 5")

    st.divider()

    res = st.session_state.run_results
    if res:
        if res["status"] == "error":
            st.error(res["message"])
        elif res["status"] == "info":
            st.info(res["message"])
        else:
            st.subheader("🧪 Результаты тестов:")
            for r in res["results"]:
                if r["passed"]: st.success(f"✅ {r['name']} — Успешно")
                else: st.error(f"❌ {r['name']} — {r['error']}")
            
            if res["passed"] == res["total"]:
                st.success("🎉 Задание решено верно!")

    if st.session_state.attempts >= 5:
        st.error("⚠️ Попытки закончились. Вот эталонное решение:")
        with st.expander("👀 Посмотреть идеальное решение", expanded=True):
            st.code(task.solution_code)