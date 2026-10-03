"""واجهة تفاعلية للتداخلات الدوائية (عربي + إنجليزي)"""

import streamlit as st
import pandas as pd
import altair as alt
from itertools import combinations
from src.database import Session, ActiveIngredient, Interaction, BrandName
from src.pdf_export import create_pdf_report
from datetime import datetime

# إعداد الصفحة
st.set_page_config(
    page_title="فحص التداخلات الدوائية",
    page_icon="💊",
    layout="wide"
)

# ===== Header =====
col_logo, col_title = st.columns([1, 5])
with col_logo:
    st.markdown("# 💊")
with col_title:
    st.title("فحص التداخلات الدوائية")
    st.markdown("أداة تفاعلية لفحص التداخلات الدوائية بين المواد الفعالة")

st.markdown("---")

st.markdown(
    """
    <div style='text-align: center; color: #7f8c8d; font-size: 14px; padding: 10px;'>
        👨‍💻 تطوير: <b> Dr.Mostafa Sayed </b> | 📅 2026
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown("---")


# ==================== الدوال ====================

def get_all_ingredients():
    """جلب كل المواد (اسم + اسم عربي) + الأسماء التجارية"""
    session = Session()
    try:
        items = session.query(ActiveIngredient).order_by(ActiveIngredient.name).all()

        # قاموس الأسماء التجارية: brand_name → ingredient_name
        brands = session.query(BrandName).all()
        brand_map = {}
        for b in brands:
            brand_map[b.brand_name] = b.ingredient_id

        # قاموس العرض: display_name → id
        result = {}
        for item in items:
            # الاسم الأساسي
            if item.name_ar:
                display = f"{item.name} ({item.name_ar})"
            else:
                display = item.name
            result[display] = item.id

            # الأسماء التجارية المرتبطة بالمادة دي
            for brand_name, ing_id in brand_map.items():
                if ing_id == item.id:
                    brand_display = f"{brand_name} → {item.name}"
                    result[brand_display] = item.id

        # رتّب أبجدياً
        result = dict(sorted(result.items(), key=lambda x: x[0].lower()))
        return result
    finally:
        session.close()


def get_ingredient_by_id(ing_id: int):
    """جلب مادة بالـ id"""
    session = Session()
    try:
        return session.get(ActiveIngredient, ing_id)
    finally:
        session.close()


def format_name(ing):
    """تنسيق اسم المادة (إنجليزي + عربي)"""
    if ing.name_ar:
        return f"{ing.name} ({ing.name_ar})"
    return ing.name


def get_interaction_between(id_a: int, id_b: int):
    session = Session()
    try:
        if id_a > id_b:
            id_a, id_b = id_b, id_a
        return session.query(Interaction).filter_by(
            ingredient_a_id=id_a,
            ingredient_b_id=id_b
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


# ==================== الواجهة ====================

st.subheader("📋 المواد الفعالة")

# جلب كل المواد
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
            placeholder="اكتب اسم المادة (إنجليزي أو عربي)...",
            label_visibility="collapsed"
        )
        ingredient_inputs.append(val)
    with col2:
        if st.session_state.num_fields > 2:
            if st.button("❌", key=f"del_{i}", help="امسح المادة دي"):
                remove_field(i)
                st.rerun()

col_add, col_empty = st.columns([1, 4])
with col_add:
    if st.button("➕ إضافة مادة", use_container_width=True):
        add_field()
        st.rerun()

st.markdown("---")

# زرار الفحص
if st.button("🔎 افحص التداخلات", type="primary", use_container_width=True):
    # فلترة المختار
    selected_displays = [n for n in ingredient_inputs if n]

    if len(selected_displays) < 2:
        st.warning("⚠️ اختر على الأقل مادتين")
    else:
        # جلب الـ ids
        ingredients = []
        for display in selected_displays:
            ing_id = all_ingredients.get(display)
            if ing_id:
                ing = get_ingredient_by_id(ing_id)
                if ing and not any(i.id == ing.id for i in ingredients):
                    ingredients.append(ing)

        if len(ingredients) < 2:
            st.error("❌ محتاج على الأقل مادتين")
        else:
            st.success(f"✅ هفحص **{len(ingredients)}** مادة")

            # عرض المواد
            cols = st.columns(len(ingredients))
            for i, ing in enumerate(ingredients):
                cols[i].markdown(f"**{format_name(ing)}**")

            st.markdown("---")

            # افحص كل الأزواج
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

            # ==================== النتائج ====================
            st.subheader(f"📊 نتيجة الفحص ({pairs_checked} زوج تم فحصه)")

            if not found_interactions:
                st.success("✅ **مفيش تداخلات مسجلة بين هذه المواد!**")
                st.info("💡 بس خد بالك إن القاعدة مش شاملة كل التداخلات المحتملة.")
            else:
                major = sum(1 for i in found_interactions if i["severity"] == "major")
                moderate = sum(1 for i in found_interactions if i["severity"] == "moderate")
                minor = sum(1 for i in found_interactions if i["severity"] == "minor")
                total = len(found_interactions)

                # التنبيه النصي
                if major > 0:
                    st.error(
                        f"🚨 **تحذير خطير!** فيه **{major}** تداخل دوائي خطير بين المواد دي. "
                        f"**لازم تراجع الطبيب أو الصيدلي فوراً قبل ما تاخد أي دواء.**"
                    )
                elif moderate > 0:
                    st.warning(
                        f"⚠️ **انتبه!** فيه **{moderate}** تداخل دوائي متوسط. "
                        f"**يُفضل استشارة الصيدلي قبل الاستخدام.**"
                    )
                elif minor > 0:
                    st.info(
                        f"ℹ️ فيه **{minor}** تداخل بسيط. "
                        f"**خد بالك واستشر الصيدلي لو فيه أي قلق.**"
                    )

                st.markdown("---")

                # عدادات
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("🔴 خطير", major)
                col2.metric("🟡 متوسط", moderate)
                col3.metric("🟢 بسيط", minor)
                col4.metric("📊 الإجمالي", total)

                st.markdown("---")

                # ==================== الرسوم البيانية ====================
                st.subheader("📈 ملخص مرئي")

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
                            range=["#e74c3c", "#f39c12", "#27ae60"]
                        )
                        chart = alt.Chart(chart_data).mark_bar().encode(
                            x=alt.X("الخطورة:N", sort=["خطير", "متوسط", "بسيط"], title=""),
                            y=alt.Y("العدد:Q", title="عدد التداخلات"),
                            color=alt.Color("الخطورة:N", scale=color_scale, legend=None),
                            tooltip=["الخطورة", "العدد"]
                        ).properties(height=300)
                        st.altair_chart(chart, use_container_width=True)

                with chart_col2:
                    st.markdown("**عدد التداخلات لكل مادة**")

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
                            "عدد التداخلات": list(ing_counts.values()),
                            "الخطورة": [ing_severity.get(m, "unknown") for m in ing_counts.keys()],
                        }).sort_values("عدد التداخلات", ascending=False)

                        severity_map = {
                            "major": "خطير",
                            "moderate": "متوسط",
                            "minor": "بسيط",
                            "unknown": "غير معروف"
                        }
                        df_counts["الخطورة"] = df_counts["الخطورة"].map(severity_map)

                        color_scale2 = alt.Scale(
                            domain=["خطير", "متوسط", "بسيط", "غير معروف"],
                            range=["#e74c3c", "#f39c12", "#27ae60", "#95a5a6"]
                        )
                        chart2 = alt.Chart(df_counts).mark_bar().encode(
                            x=alt.X("المادة:N", sort="-y", title=""),
                            y=alt.Y("عدد التداخلات:Q", title="عدد التداخلات"),
                            color=alt.Color("الخطورة:N", scale=color_scale2, title="أعلى خطورة"),
                            tooltip=["المادة", "عدد التداخلات", "الخطورة"]
                        ).properties(height=300)
                        st.altair_chart(chart2, use_container_width=True)

                st.markdown("---")

                # جدول
                st.subheader("📋 جدول التداخلات")

                severity_emoji = {"major": "🔴", "moderate": "🟡", "minor": "🟢", "unknown": "⚪"}
                severity_text = {"major": "خطير", "moderate": "متوسط", "minor": "بسيط", "unknown": "غير معروف"}

                table_data = []
                for inter in found_interactions:
                    table_data.append({
                        "الخطورة": f"{severity_emoji[inter['severity']]} {severity_text[inter['severity']]}",
                        "المادة 1": inter["a"],
                        "المادة 2": inter["b"],
                        "الوصف": inter["description"],
                        "التوصية": inter["management"],
                    })

                df_table = pd.DataFrame(table_data)
                st.dataframe(df_table, use_container_width=True, hide_index=True)

                st.markdown("---")

                # تفاصيل
                st.subheader("📖 تفاصيل كل تداخل")

                severity_icons = {
                    "major": "🔴 خطير",
                    "moderate": "🟡 متوسط",
                    "minor": "🟢 بسيط",
                    "unknown": "⚪ غير معروف",
                }

                for inter in found_interactions:
                    icon = severity_icons.get(inter["severity"], "⚪")
                    with st.expander(f"{icon} — **{inter['a']}** + **{inter['b']}**"):
                        st.markdown(f"**📋 الوصف:** {inter['description']}")
                        st.markdown(f"**💊 التوصية:** {inter['management']}")

                    # ملخص كل الأزواج
            st.markdown("---")
            with st.expander(f"🔬 كل الأزواج اللي افحصت ({pairs_checked})"):
                for ing_a, ing_b in combinations(ingredients, 2):
                    inter = get_interaction_between(ing_a.id, ing_b.id)
                    status = "⚠️ فيه تداخل" if inter else "✅ مفيش"
                    st.write(f"- {format_name(ing_a)} + {format_name(ing_b)}: {status}")

            # ==================== تصدير PDF ====================
            st.markdown("---")
            st.subheader("📄 حمّل التقرير")

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
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"❌ خطأ في إنشاء التقرير: {e}")


# ===== Footer =====
st.markdown("---")

# إخلاء المسؤولية
st.warning(
    "⚠️ **إخلاء مسؤولية**: هذه الأداة لأغراض تعليمية فقط ولا تُغني عن استشارة "
    "الطبيب أو الصيدلي. لا تتخذ أي قرار علاجي بناءً على نتائجها."
)

# المصادر
with st.expander("📚 المصادر والمراجع"):
    st.markdown(
        """
        ### 🔬 مصادر البيانات
        
        - **RxNorm** (المكتبة الوطنية الأمريكية للطب - NLM)
          - استخدام: أسماء المواد الفعالة، أكواد RXCUI
          - الرخصة: ملك عام (Public Domain)
          - [الموقع الرسمي](https://www.nlm.nih.gov/research/umls/rxnorm/)
        
        - **DDInter 2.0** (قاعدة بيانات التداخلات الدوائية)
          - استخدام: بيانات التداخلات الدوائية ودرجات الخطورة
          - الرخصة: CC BY-NC-SA 4.0
          - [الموقع الرسمي](http://ddinter.scbdd.com/)
        
        - **openFDA** (إدارة الغذاء والدواء الأمريكية - FDA)
          - استخدام: بيانات الملصقات الدوائية
          - الرخصة: ملك عام (Public Domain)
          - [الموقع الرسمي](https://open.fda.gov/)
        
        ### 💻 التقنيات المستخدمة
        
        - **Python 3.10** - لغة البرمجة
        - **Streamlit** - إطار عمل الواجهة التفاعلية
        - **SQLAlchemy** - التعامل مع قاعدة البيانات
        - **SQLite** - قاعدة البيانات
        - **ReportLab** - تصدير PDF
        - **Altair** - الرسوم البيانية
        - **Arabic Reshaper + python-bidi** - دعم اللغة العربية
        
        ### ⚖️ ملاحظات قانونية
        
        - البيانات المستخدمة من DDInter مرخصة تحت **CC BY-NC-SA 4.0**
        - **الاستخدام التجاري غير مسموح** بهذه البيانات
        - الأداة متاحة للاستخدام التعليمي والشخصي فقط
        
        ### 📧 للتواصل
        
        - المطور: **Dr.Mostafa Sayed**
        """
    )

st.caption("© 2026 - جميع الحقوق محفوظة | صُنع بـ ❤️ في مصر")