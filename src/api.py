"""اختبار البحث عن التداخلات الدوائية"""

from src.database import Session, ActiveIngredient, Interaction


def find_interactions(ingredient_name: str):
    """يبحث عن كل التداخلات لمادة فعالة معينة"""
    session = Session()

    try:
        # ابحث عن المادة (بحث غير حساس لحالة الأحرف)
        ingredient = session.query(ActiveIngredient).filter(
            ActiveIngredient.name.ilike(ingredient_name)
        ).first()

        if not ingredient:
            print(f"❌ مش لاقي مادة باسم: {ingredient_name}")
            return

        print(f"\n🔍 المادة: {ingredient.name} (RXCUI: {ingredient.rxnorm_cui})")
        print("=" * 60)

        # ابحث عن كل التداخلات
        interactions = session.query(Interaction).filter(
            (Interaction.ingredient_a_id == ingredient.id) |
            (Interaction.ingredient_b_id == ingredient.id)
        ).all()

        if not interactions:
            print("✅ مفيش تداخلات مسجلة لهذه المادة")
            return

        print(f"⚠️ عدد التداخلات: {len(interactions)}\n")

        # رتّب حسب الخطورة
        severity_order = {"major": 1, "moderate": 2, "minor": 3, "unknown": 4}
        interactions.sort(key=lambda x: severity_order.get(x.severity, 5))

        severity_icons = {
            "major": "🔴 خطير",
            "moderate": "🟡 متوسط",
            "minor": "🟢 بسيط",
            "unknown": "⚪ غير معروف"
        }

        for inter in interactions:
            # اعرف المادة التانية
            other_id = inter.ingredient_b_id if inter.ingredient_a_id == ingredient.id else inter.ingredient_a_id
            other = session.query(ActiveIngredient).get(other_id)

            print(f"{severity_icons.get(inter.severity, '⚪')} — مع: {other.name}")
            print(f"   📋 {inter.description}")
            print(f"   💊 {inter.management}")
            print()

    finally:
        session.close()


if __name__ == "__main__":
    print("🧪 اختبار البحث عن التداخلات\n")

    # جرّب مواد مختلفة
    for name in ["ibuprofen", "warfarin", "aspirin"]:
        find_interactions(name)
        print("\n" + "=" * 60 + "\n")
