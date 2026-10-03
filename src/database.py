from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import os

# مسار قاعدة البيانات
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "drugs.db")

# إنشاء الـ engine
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine)


class ActiveIngredient(Base):
    """جدول المواد الفعالة"""
    __tablename__ = "active_ingredients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    name_ar = Column(String(255))
    rxnorm_cui = Column(String(20), unique=True)
    atc_code = Column(String(20))

    def __repr__(self):
        return f"<ActiveIngredient(name='{self.name}', rxcui='{self.rxnorm_cui}')>"

class BrandName(Base):
    """جدول الأسماء التجارية"""
    __tablename__ = "brand_names"

    id = Column(Integer, primary_key=True, autoincrement=True)
    brand_name = Column(String(255), nullable=False, unique=True)
    ingredient_id = Column(Integer, ForeignKey("active_ingredients.id"), nullable=False)

    def __repr__(self):
        return f"<BrandName(brand='{self.brand_name}', ing_id={self.ingredient_id})>"


class Interaction(Base):
    """جدول التداخلات الدوائية"""
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ingredient_a_id = Column(Integer, ForeignKey("active_ingredients.id"), nullable=False)
    ingredient_b_id = Column(Integer, ForeignKey("active_ingredients.id"), nullable=False)
    severity = Column(String(20), nullable=False)
    description = Column(Text)
    management = Column(Text)
    source = Column(String(50))

    __table_args__ = (
        CheckConstraint("severity IN ('major','moderate','minor','unknown')", name="check_severity"),
        CheckConstraint("ingredient_a_id < ingredient_b_id", name="check_order"),
    )

    def __repr__(self):
        return f"<Interaction(a={self.ingredient_a_id}, b={self.ingredient_b_id}, sev='{self.severity}')>"


def init_db():
    """إنشاء الجداول"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    Base.metadata.create_all(engine)
    print(f"✅ قاعدة البيانات اتعملت في: {DB_PATH}")


if __name__ == "__main__":
    init_db()
