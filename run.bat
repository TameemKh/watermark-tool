@echo off

:: تشغيل كل شيء داخل cmd.exe صريح
cmd.exe /k "cd /d %~dp0 && echo. && echo  ========================================= && echo    IVR Watermark Tool - جاري التشغيل... && echo  ========================================= && echo. && echo [1/2] التحقق من المكتبات المطلوبة... && pip install -r requirements.txt --quiet && echo. && echo [2/2] تشغيل الأداة... سيفتح المتصفح تلقائياً && echo. && streamlit run app.py --server.headless false"
