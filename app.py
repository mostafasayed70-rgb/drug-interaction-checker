"""واجهة تفاعلية للتداخلات الدوائية - تصميم Modern Medical + Playful"""

import streamlit as st
import pandas as pd
import altair as alt
from itertools import combinations
from datetime import datetime
from src.database import Session, ActiveIngredient, Interaction, BrandName
from src.pdf_export import create_pdf_report

# ==================== إعداد الصفحة ====================
st.set_page_config(
    page_title="فحص التداخلات الدوائية",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================== CSS مخصص ====================
st.markdown("""
<style>
    /* استيراد الخطوط */
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&family=Inter:wght@400;500;600;700&display=swap');
    
    /* التنسيق العام */
    html, body, [class*="css"] {
        font-family: 'Cairo', 'Inter', sans-serif;
    }
    
    /* الخلفية بتدرج */
    .stApp {
        background: linear-gradient(135deg, #F8FAFC 0%, #E8F4F8 50%, #F0F9FF 100%);
    }
    
    /* Header رئيسي */
    .main-header {
        background: linear-gradient(135deg, #4A90E2 0%, #26D0CE 100%);
        padding: 2.5rem 2rem;
        border-radius: 20px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(74, 144, 226, 0.3);
        animation: fadeInDown 0.8s ease-out;
    }
    
    .main-header h1 {
        color: white !important;
        font-size: 2.5rem;
        margin: 0;
        font-weight: 900;
        text-align: center;
    }
    
    .main-header p {
        color: rgba(255,255,255,0.95);
        font-size: 1.1rem;
        text-align: center;
        margin-top: 0.5rem;
    }
    
    .dev-badge {
        text-align: center;
        color: white;
        font-size: 0.9rem;
        margin-top: 1rem;
        opacity: 0.95;
    }
    
    /* كروت المواد */
    .ingredient-card {
        background: white;
        padding: 1rem 1.5rem;
        border-radius: 15px;
        border-right: 4px solid #4A90E2;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        margin: 0.5rem 0;
        animation: slideInRight 0.5s ease-out;
    }
    
    /* بطاقة النتيجة - خطير */
    .result-card-major {
        background: linear-gradient(135deg, #FFE5E5 0%, #FFD0D0 100%);
        border-right: 6px solid #E74C3C;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(231, 76, 60, 0.15);
        animation: slideInUp 0.5s ease-out;
    }
    
    /* بطاقة النتيجة - متوسط */
    .result-card-moderate {
        background: linear-gradient(135deg, #FFF5E5 0%, #FFE8C0 100%);
        border-right: 6px solid #F39C12;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(243, 156, 18, 0.15);
        animation: slideInUp 0.5s ease-out;
    }
    
    /* بطاقة النتيجة - بسيط */
    .result-card-minor {
        background: linear-gradient(135deg, #E5F8F0 0%, #D0F0E0 100%);
        border-right: 6px solid #27AE60;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(39, 174, 96, 0.15);
        animation: slideInUp 0.5s ease-out;
    }
    
    .result-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.8rem;
    }
    
    .result-desc {
        color: #475569;
        margin: 0.5rem 0;
        line-height: 1.6;
    }
    
    /* Metric Cards */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        transition: transform 0.3s ease;
        animation: popIn 0.5s ease-out;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
    }
    
    .metric-number {
        font-size: 2.5rem;
        font-weight: 900;
        margin: 0.5rem 0;
    }
    
    .metric-label {
        font-size: 0.95rem;
        color: #64748B;
        font-weight: 600;
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 0.35rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 700;
        margin: 0.2rem;
    }
    
    .badge-major { background: #E74C3C; color: white; }
    .badge-moderate { background: #F39C12; color: white; }
    .badge-minor { background: #27AE60; color: white; }
    
    /* زرار أساسي */
    .stButton > button {
        background: linear-gradient(135deg, #4A90E2 0%, #26D0CE 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.7rem 2rem;
        font-weight: 700;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(74, 144, 226, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(74, 144, 226, 0.4);
    }
    
    /* Animations */
    @keyframes fadeInDown {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes slideInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes slideInRight {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    @keyframes popIn {
        0% { opacity: 0; transform: scale(0.8); }
        100% { opacity: 1; transform: scale(1); }
    }
    
    /* Input Fields */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > div {
        border-radius: 12px !important;
        border: 2px solid #E2E8F0 !important;
        padding: 0.6rem 1rem !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > div:focus-within {
        border-color: #4A90E2 !important;
        box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1) !important;
    }
    
    /* إخفاء قائمة Streamlit */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ==================== الدوال ====================

def get_all_ingredients():
    """جلب كل المواد (اسم + اسم عربي + أسماء تجارية)"""
    session = Session()
    try:
        items = session.query(ActiveIngredient).order_by(ActiveIngredient.name).all()
        brands = session.query(BrandName).all()
        brand_map = {b.brand_name: b.ingredient_id for b in brands}

        result = {}
        for item in items:
            if item.name_ar:
                display = f"{item.name} ({item.name_ar})"
            else:
                display = item.name
            result[display] = item.id
            for brand_name, ing_id in brand_map.items():
                if ing_id == item.id:
                    result[f"{brand_name} → {item.name}"] = item.id

        return dict(sorted(result.items(), key=lambda x: x[0].lower()))
    finally:
        session.close()


def get_ingredient_by_id(ing_id: int):
    session = Session()
    try:
        return session.get(ActiveIngredient, ing_id)
    finally:
        session.close()


def format_name(ing):
    if ing.name_ar:
        return f"{ing.name} ({ing.name_ar})"
    return ing.name


def get_interaction_between(id_a: int, id_b: int):
    session = Session()
    try:
        if id_a > id_b:
            id_a, id_b = id_b, id_a
        return session.query(Interaction).filter_by(
            ingredient_a_id=id_a, ingredient_b_id=id_b
        ).first()
    finally:
        session.close()


# ==================== إدارة الحالة ====================
if "num_fields" not in st.session_state:
    st.session_state.num_fields = 2


def add_field():
    st.session_state.num_fields += 1


def remove_field(idx):
    if st.session_state.num_fields > 2:
        st.session_state.num_fields -= 1


# ==================== Header ====================
st.markdown("""
<div class="main-header">
    <h1>💊 فحص التداخلات الدوائية</h1>
    <p>أداة تفاعلية ذكية لفحص التداخلات الدوائية بين المواد الفعالة</p>
    <div class="dev-badge">👨‍💻 تطوير: <b>Dr. Mostafa Sayed</b> | 📅 2026</div>
</div>
""", unsafe_allow_html=True)


# ==================== الواجهة ====================
st.markdown("### 📋 المواد الفعالة")

all_ingredients = get_all_ingredients()
options_list = list(all_ingredients.keys())

ingredient_inputs = []
for i in range(st.session_state.num_fields):
    col1, col2 = st.columns([5, 1])
    with col1:
        val = st.selectbox(
            f"المادة {i+1}",
            options=options_list,
            index=None,
            key=f"ing_{i}",
            placeholder="🔍 اكتب اسم المادة (إنجليزي أو عربي)...",
            label_visibility="collapsed"
        )
        ingredient_inputs.append(val if val else "")
    with col2:
        if st.session_state.num_fields > 2:
            if st.button("❌", key=f"del_{i}", help="امسح المادة"):
                remove_field(i)
                st.rerun()

col_add, col_empty = st.columns([1, 4])
with col_add:
    if st.button("➕ إضافة مادة", width='stretch'):
        add_field()
        st.rerun()

st.markdown("---")

# زرار الفحص
if st.button("🔎 افحص التداخلات", type="primary", width='stretch'):
    names = [n for n in ingredient_inputs if n]

    if len(names) < 2:
        st.warning("⚠️ اختر على الأقل مادتين")
    else:
        ingredients = []
        for display in names:
            ing_id = all_ingredients.get(display)
            if ing_id:
                ing = get_ingredient_by_id(ing_id)
                if ing and not any(i.id == ing.id for i in ingredients):
                    ingredients.append(ing)

        if len(ingredients) < 2:
            st.error("❌ محتاج على الأقل مادتين")
        else:
            st.markdown(f"### ✅ هفحص **{len(ingredients)}** مادة")

            # كروت المواد
            cols = st.columns(min(len(ingredients), 4))
            for i, ing in enumerate(ingredients):
                with cols[i % 4]:
                    st.markdown(f"""
                    <div class="ingredient-card">
                        💊 <b>{format_name(ing)}</b>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("---")

            # فحص الأزواج
            found_interactions = []
            pairs_checked = 0

            for ing_a, ing_b in combinations(ingredients, 2):
                pairs_checked += 1
                inter = get_interaction_between(ing_a.id, ing_b.id)
                if inter:
                    found_interactions.append({
                        "a": format_name(ing_a),
                        "b": format_name(ing_b),
                        "severity": inter.severity,
                        "description": inter.description,
                        "management": inter.management,
                    })

            severity_order = {"major": 1, "moderate": 2, "minor": 3, "unknown": 4}
            found_interactions.sort(key=lambda x: severity_order.get(x["severity"], 5))

            # النتائج
            st.markdown(f"## 📊 نتيجة الفحص ({pairs_checked} زوج)")

            if not found_interactions:
                st.success("✅ **مفيش تداخلات مسجلة بين هذه المواد!**")
                st.info("💡 القاعدة مش شاملة كل التداخلات المحتملة.")
            else:
                major = sum(1 for i in found_interactions if i["severity"] == "major")
                moderate = sum(1 for i in found_interactions if i["severity"] == "moderate")
                minor = sum(1 for i in found_interactions if i["severity"] == "minor")

                # تنبيه
                if major > 0:
                    st.error(f"🚨 **تحذير خطير!** فيه **{major}** تداخل خطير. راجع الطبيب فوراً.")
                elif moderate > 0:
                    st.warning(f"⚠️ **انتبه!** فيه **{moderate}** تداخل متوسط. استشر الصيدلي.")
                elif minor > 0:
                    st.info(f"ℹ️ فيه **{minor}** تداخل بسيط.")

                # Metric Cards
                st.markdown("### 📈 ملخص")
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div style="font-size:1.5rem">🔴</div>
                        <div class="metric-number" style="color:#E74C3C">{major}</div>
                        <div class="metric-label">خطير</div>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div style="font-size:1.5rem">🟡</div>
                        <div class="metric-number" style="color:#F39C12">{moderate}</div>
                        <div class="metric-label">متوسط</div>
                    </div>
                    """, unsafe_allow_html=True)

                with col3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div style="font-size:1.5rem">🟢</div>
                        <div class="metric-number" style="color:#27AE60">{minor}</div>
                        <div class="metric-label">بسيط</div>
                    </div>
                    """, unsafe_allow_html=True)

                with col4:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div style="font-size:1.5rem">📊</div>
                        <div class="metric-number" style="color:#4A90E2">{len(found_interactions)}</div>
                        <div class="metric-label">الإجمالي</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("---")

                # تفاصيل التداخلات - Cards
                st.markdown("### 📖 تفاصيل التداخلات")

                for inter in found_interactions:
                    sev = inter["severity"]
                    if sev == "major":
                        card_class = "result-card-major"
                        badge_class = "badge-major"
                        badge_text = "🔴 خطير"
                    elif sev == "moderate":
                        card_class = "result-card-moderate"
                        badge_class = "badge-moderate"
                        badge_text = "🟡 متوسط"
                    else:
                        card_class = "result-card-minor"
                        badge_class = "badge-minor"
                        badge_text = "🟢 بسيط"

                    st.markdown(f"""
                    <div class="{card_class}">
                        <span class="badge {badge_class}">{badge_text}</span>
                        <div class="result-title" style="margin-top:0.5rem">
                            💊 {inter['a']} <span style="color:#94A3B8">+</span> {inter['b']}
                        </div>
                        <div class="result-desc">📋 <b>الوصف:</b> {inter['description']}</div>
                        <div class="result-desc">💡 <b>التوصية:</b> {inter['management']}</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("---")

                # Chart
                st.markdown("### 📊 ملخص مرئي")

                chart_col1, chart_col2 = st.columns(2)

                with chart_col1:
                    st.markdown("**توزيع التداخلات حسب الخطورة**")
                    chart_data = pd.DataFrame({
                        "الخطورة": ["خطير", "متوسط", "بسيط"],
                        "العدد": [major, moderate, minor]
                    })
                    chart_data = chart_data[chart_data["العدد"] > 0]
                    if not chart_data.empty:
                        color_scale = alt.Scale(
                            domain=["خطير", "متوسط", "بسيط"],
                            range=["#E74C3C", "#F39C12", "#27AE60"]
                        )
                        chart = alt.Chart(chart_data).mark_arc(innerRadius=50).encode(
                            theta=alt.Theta("العدد:Q"),
                            color=alt.Color("الخطورة:N", scale=color_scale),
                            tooltip=["الخطورة", "العدد"]
                        ).properties(height=300)
                        st.altair_chart(chart, width='stretch')

                with chart_col2:
                    st.markdown("**التداخلات لكل مادة**")
                    severity_rank = {"major": 3, "moderate": 2, "minor": 1, "unknown": 0}
                    ing_severity = {}
                    ing_counts = {}

                    for inter in found_interactions:
                        for ing in [inter["a"], inter["b"]]:
                            ing_counts[ing] = ing_counts.get(ing, 0) + 1
                            current_rank = severity_rank.get(inter["severity"], 0)
                            if ing not in ing_severity or severity_rank.get(ing_severity[ing], 0) < current_rank:
                                ing_severity[ing] = inter["severity"]

                    if ing_counts:
                        df_counts = pd.DataFrame({
                            "المادة": list(ing_counts.keys()),
                            "عدد": list(ing_counts.values()),
                        }).sort_values("عدد", ascending=True)
                        chart2 = alt.Chart(df_counts).mark_bar(
                            color="#4A90E2", cornerRadiusEnd=8
                        ).encode(
                            x=alt.X("عدد:Q", title="عدد التداخلات"),
                            y=alt.Y("المادة:N", sort="-x", title=""),
                        ).properties(height=300)
                        st.altair_chart(chart2, width='stretch')

                st.markdown("---")

                # PDF
                st.markdown("### 📄 حمّل التقرير")
                ingredient_names = [format_name(ing) for ing in ingredients]
                try:
                    pdf_buffer = create_pdf_report(
                        ingredients=ingredient_names,
                        interactions=found_interactions,
                        pairs_checked=pairs_checked
                    )
                    st.download_button(
                        label="📥 حمّل التقرير PDF",
                        data=pdf_buffer,
                        file_name=f"drug_interactions_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf",
                        width='stretch',
                    )
                except Exception as e:
                    st.error(f"❌ خطأ في إنشاء التقرير: {e}")

            # ملخص كل الأزواج
            with st.expander(f"🔬 كل الأزواج اللي افحصت ({pairs_checked})"):
                for ing_a, ing_b in combinations(ingredients, 2):
                    inter = get_interaction_between(ing_a.id, ing_b.id)
                    status = "⚠️ فيه تداخل" if inter else "✅ مفيش"
                    st.write(f"- {format_name(ing_a)} + {format_name(ing_b)}: {status}")


# ==================== Footer ====================
st.markdown("---")
st.warning("⚠️ **إخلاء مسؤولية**: هذه الأداة تعليمية فقط ولا تُغني عن استشارة الطبيب أو الصيدلي.")

with st.expander("📚 المصادر والمراجع"):
    st.markdown("""
    ### 🔬 مصادر البيانات
    - **RxNorm** (NLM) - أسماء المواد الفعالة
    - **DDInter 2.0** - بيانات التداخلات (CC BY-NC-SA 4.0)
    - **openFDA** - الملصقات الدوائية
    
    ### 💻 التقنيات
    Python 3.10 • Streamlit • SQLAlchemy • SQLite • ReportLab • Altair
    
    ### 👨‍💻 المطور
    **Dr. Mostafa Sayed**
    """)

st.caption("© 2026 - صُنع بـ ❤️ في مصر")