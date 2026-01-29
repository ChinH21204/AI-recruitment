# Script khởi động hệ thống AI Recruitment + QLNS Demo
Write-Host "`n╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  KHỞI ĐỘNG HỆ THỐNG AI RECRUITMENT + QLNS            ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# 1. Laravel Backend
Write-Host "[1/3] Khởi động Laravel Backend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\folder systemn\cs_462_i_be'; php artisan serve --host=127.0.0.1 --port=8000"
Start-Sleep -Seconds 2

# 2. Vue Frontend
Write-Host "[2/3] Khởi động Vue Frontend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\folder systemn\cs_462_i_fe'; npm run dev"
Start-Sleep -Seconds 2

# 3. FastAPI AI Service
Write-Host "[3/3] Khởi động FastAPI AI Service..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; .\venv\Scripts\Activate.ps1; cd app; python -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload"
Start-Sleep -Seconds 3

Write-Host "`n✅ Đã khởi động tất cả services!`n" -ForegroundColor Green
Write-Host "📋 Truy cập:" -ForegroundColor Cyan
Write-Host "   • Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "   • Backend API: http://127.0.0.1:8000" -ForegroundColor White
Write-Host "   • AI API Docs: http://127.0.0.1:8001/docs`n" -ForegroundColor White

Write-Host "🎯 Hướng dẫn demo:" -ForegroundColor Yellow
Write-Host "   1. Mở trình duyệt: http://localhost:5173" -ForegroundColor White
Write-Host "   2. Đăng nhập vào hệ thống" -ForegroundColor White
Write-Host "   3. Vào menu 'Hồ sơ ứng tuyển'" -ForegroundColor White
Write-Host "   4. Tạo hồ sơ mới → AI sẽ tự động đánh giá CV" -ForegroundColor White
Write-Host "   5. Xem điểm AI và đánh giá trong danh sách`n" -ForegroundColor White

