@echo off
cd /d C:\Users\LOQ\drug-interaction-checker
call venv\Scripts\activate
echo.
echo ========================================
echo   تشغيل تطبيق فحص التداخلات الدوائية
echo ========================================
echo.
start http://127.0.0.1:8501
streamlit run app.py --server.port=8501
pause