@echo off
chcp 65001 > nul
echo ========================================
echo 自动输入工具 - 打包脚本
echo ========================================
echo.

:: 检查是否安装了PyInstaller
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [1/3] 正在安装 PyInstaller...
    pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple
    if errorlevel 1 (
        echo 安装 PyInstaller 失败！请检查网络连接或手动安装。
        pause
        exit /b 1
    )
    echo PyInstaller 安装完成！
    echo.
) else (
    echo [1/3] PyInstaller 已安装
    echo.
)

:: 清理旧的打包文件
echo [2/3] 清理旧的打包文件...
if exist "dist" (
    rmdir /s /q "dist"
)
if exist "build" (
    rmdir /s /q "build"
)
echo 清理完成！
echo.

:: 开始打包
echo [3/3] 开始打包应用程序...
echo 这可能需要几分钟时间，请耐心等待...
echo.

:: 使用完整路径调用虚拟环境中的 python
"%~dp0.venv\Scripts\python.exe" -m PyInstaller build.spec --clean --noconfirm

:: 检查打包是否成功
if errorlevel 1 (
    echo.
    echo ========================================
    echo 打包失败！请检查错误信息。
    echo ========================================
    pause
    exit /b 1
)

echo.
echo ========================================
echo 打包成功！
echo ========================================
echo.
echo 可执行文件位置: dist\自动输入工具.exe
echo.
echo 你可以将 dist 文件夹中的 "自动输入工具.exe" 复制到任何地方运行
echo 注意：首次运行时会在同目录下生成 config.json 配置文件
echo.

:: 创建发布文件夹
echo 正在创建发布包...
if exist "发布包" (
    rmdir /s /q "发布包"
)
mkdir "发布包"
copy "dist\自动输入工具.exe" "发布包\"
copy "logo.ico" "发布包\" 2>nul
copy "logo.png" "发布包\" 2>nul
copy "README.md" "发布包\" 2>nul
copy "LICENSE" "发布包\" 2>nul

echo.
echo 发布包已创建在 "发布包" 文件夹中！
echo 你可以直接分发该文件夹中的内容。
echo.
pause