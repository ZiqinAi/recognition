// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 获取DOM元素
    const selectFileBtn = document.getElementById('selectFileBtn');
    const imageInput = document.getElementById('imageInput');
    const previewImage = document.getElementById('previewImage');
    const executeOcrBtn = document.getElementById('executeOcrBtn');
    const zoomSlider = document.getElementById('zoomSlider');
    const zoomValue = document.getElementById('zoomValue');
    const logBox = document.getElementById('logBox');
    const ocrResultBox = document.getElementById('ocrResultBox');
    const ocrTable = document.getElementById('ocrTable').getElementsByTagName('tbody')[0];
    const imageModal = new bootstrap.Modal(document.getElementById('imageModal'));
    const modalImage = document.getElementById('modalImage');
    const useDefaultImgBtn = document.getElementById('useDefaultImgBtn'); // 新增默认图像按钮
    
    // 图像预处理相关元素
    const preprocessToggle = document.getElementById('preprocessToggle');
    const preprocessOptions = document.getElementById('preprocessOptions');
    
    // 变量
    let currentImagePath = null;
    let currentFullPath = null;
    let currentImageId = null;
    let currentScale = 1;
    const defaultImagePath = 'TheFirst/static/images/placeholder.jpg'; // 默认图像路径
    const default_image_path = 'static/images/placeholder.jpg' // 默认图像路径

    
    // 添加日志的函数
    function addLog(message, isError = false) {
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry' + (isError ? ' log-error' : '');
        logEntry.textContent = message;
        logBox.appendChild(logEntry);
        logBox.scrollTop = logBox.scrollHeight;
    }
    
    // 清除OCR结果表格
    function clearOcrTable() {
        ocrTable.innerHTML = '';
    }
    
    // 选择文件按钮点击事件
    selectFileBtn.addEventListener('click', function() {
        imageInput.click();
    });
    
    // 使用默认图像按钮点击事件
    useDefaultImgBtn.addEventListener('click', function() {
        // 记录当前默认图像信息
        currentImagePath = default_image_path;
        
        // 注册默认图像
        registerDefaultImage();
    });
    
    // 注册默认图像函数
    function registerDefaultImage() {
        // 显示加载指示器
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'loading';
        document.getElementById('imageContainer').appendChild(loadingDiv);
        
        addLog('使用默认样例图像');
        
        // 设置默认图像信息，无需API调用
        currentImagePath = default_image_path;  // 图像显示路径
        currentFullPath = defaultImagePath;  // 图像运行路径
        currentImageId = 'default_sample';   // 使用固定ID标识默认图像
        
        // 确保显示默认图像
        previewImage.src = currentImagePath;
        
        // 短暂延迟以便用户看到加载过程
        setTimeout(() => {
            // 移除加载指示器
            loadingDiv.remove();
            
            // 启用OCR按钮
            executeOcrBtn.disabled = false;
            addLog('默认样例图像已准备就绪，可以开始识别');
        }, 500);
        
        /* 以下注释掉API调用代码，因为后端未实现该API
        // 发送注册默认图像请求
        fetch('/api/register_default', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ default_image: true })
        })
        .then(response => response.json())
        .then(data => {
            // 移除加载指示器
            loadingDiv.remove();
            
            if (data.error) {
                addLog(`注册默认图像错误: ${data.error}`, true);
                return;
            }
            
            // 更新图像信息
            currentImagePath = data.image_path || defaultImagePath;
            currentFullPath = data.full_path;  // 保存完整路径
            currentImageId = data.image_id;    // 保存图片ID
            
            // 确保显示默认图像
            previewImage.src = currentImagePath;
            addLog(`默认图像已注册: ${data.image_id}`);
            
            // 启用OCR按钮
            executeOcrBtn.disabled = false;
        })
        .catch(error => {
            // 移除加载指示器
            loadingDiv.remove();
            addLog(`注册默认图像异常: ${error.message}`, true);
            
            // 应急处理 - 直接启用OCR按钮
            // 这允许在后端API不支持的情况下仍能继续
            currentImagePath = defaultImagePath;
            executeOcrBtn.disabled = false;
            addLog('已启用样例图像识别功能');
        });
        */
    }
    
    // 文件选择变更事件
    imageInput.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            const file = e.target.files[0];
            
            // 显示加载指示器
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'loading';
            document.getElementById('imageContainer').appendChild(loadingDiv);
            
            addLog(`选择文件: ${file.name}`);
            
            // 创建FormData对象并添加文件
            const formData = new FormData();
            formData.append('image', file);
            
            // 发送文件上传请求
            fetch('/api/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                // 移除加载指示器
                loadingDiv.remove();
                
                if (data.error) {
                    addLog(`上传错误: ${data.error}`, true);
                    return;
                }
                
                // 显示上传的图像
                currentImagePath = data.image_path;
                currentFullPath = data.full_path;  // 保存完整路径
                currentImageId = data.image_id;    // 保存图片ID
                previewImage.src = currentImagePath;
                addLog(`文件上传成功: ${currentImagePath}`);
                
                // 启用OCR按钮
                executeOcrBtn.disabled = false;
            })
            .catch(error => {
                // 移除加载指示器
                loadingDiv.remove();
                addLog(`上传异常: ${error.message}`, true);
            });
        }
    });
    
    // 缩放滑块事件
    zoomSlider.addEventListener('input', function() {
        currentScale = this.value / 100;
        zoomValue.textContent = `${this.value}%`;
        previewImage.style.transform = `scale(${currentScale})`;
    });
    
    // 预处理选项切换
    preprocessToggle.addEventListener('change', function() {
        const options = document.querySelectorAll('.preprocess-option');
        if (this.checked) {
            options.forEach(option => option.disabled = false);
        } else {
            options.forEach(option => option.disabled = true);
        }
    });
    
    // 执行OCR按钮点击事件
    executeOcrBtn.addEventListener('click', function() {
        if (!currentImagePath) {
            addLog('错误: 未选择图像文件', true);
            return;
        }
        
        // 收集设置参数
        const detMode = document.getElementById('detModeSelect').value;
        const charOcr = document.querySelector('input[name="detMode"]:checked').value === 'true';
        const imageSize = parseInt(document.getElementById('imageSizeInput').value);
        const version = document.getElementById('versionSelect').value;
        
        // 获取预处理选项
        const preprocessing = preprocessToggle.checked;
        const preprocess_options = {
            auto_deskew: preprocessing && document.getElementById('autoDeskewCheck').checked,
            enhance_contrast: preprocessing && document.getElementById('contrastCheck').checked,
            noise_reduction: preprocessing && document.getElementById('noiseCheck').checked,
            sharpen: preprocessing && document.getElementById('sharpenCheck').checked
        };
        
        // 添加当前识别参数信息到日志
        const versionText = version === 'default' ? '标准版本' : '古籍语序优化版本';
        const detModeText = detMode === 'sp' ? '竖排' : (detMode === 'hp' ? '横排' : '自动');
        const detTypeText = charOcr ? '单字检测识别' : '文本行检测识别';
        
        addLog(`识别参数信息:`);
        addLog(`- 识别版本: ${versionText}`);
        addLog(`- 文字排版方向: ${detModeText}`);
        addLog(`- 检测模式: ${detTypeText}`);
        addLog(`- 图片尺寸: ${imageSize}px`);
        addLog(`- 图像预处理: ${preprocessing ? '开启' : '关闭'}`);
        
        if (preprocessing) {
            addLog(`  - 自动校正倾斜: ${preprocess_options.auto_deskew ? '是' : '否'}`);
            addLog(`  - 增强对比度: ${preprocess_options.enhance_contrast ? '是' : '否'}`);
            addLog(`  - 降噪处理: ${preprocess_options.noise_reduction ? '是' : '否'}`);
            addLog(`  - 锐化处理: ${preprocess_options.sharpen ? '是' : '否'}`);
        }
        
        // 显示加载指示器
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'loading';
        document.getElementById('imageContainer').appendChild(loadingDiv);
        
        addLog('开始执行OCR处理...');
        
        // 准备OCR请求数据
        const ocrData = {
            image_path: currentImagePath,
            full_path: currentFullPath,       // 添加完整路径
            image_id: currentImageId,         // 添加图片ID
            det_mode: detMode,                // 检测模式
            image_size: imageSize,            // 图像大小
            char_ocr: charOcr,                // 单字识别
            return_position: true,            // 返回位置信息
            return_choices: true,             // 返回选项信息
            version: version,                 // 版本
            preprocess: preprocessing,        // 预处理开关
            preprocess_options: preprocess_options, // 预处理选项
            is_default_image: currentImagePath === defaultImagePath // 标记是否为默认图像
        };
        
        // 发送OCR请求
        fetch('/api/ocr', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(ocrData)
        })
        .then(response => response.json())
        .then(data => {
            // 移除加载指示器
            loadingDiv.remove();
            
            if (data.error) {
                addLog(`OCR处理错误: ${data.error}`, true);
                return;
            }
            
            // 处理OCR结果
            processOcrResult(data);
            addLog('OCR处理完成');
        })
        .catch(error => {
            // 移除加载指示器
            loadingDiv.remove();
            addLog(`OCR处理异常: ${error.message}`, true);
        });
    });
    
    // 处理OCR结果数据
    function processOcrResult(data) {
        // 更新预览图为处理后的图像
        if (data.processed_image) {
            previewImage.src = data.processed_image;
        }
        
        // 清除原有OCR结果
        ocrResultBox.innerHTML = '';
        clearOcrTable();
        
        // 显示文本内容结果
        if (data.ocr_result && data.ocr_result.data && data.ocr_result.data.text_lines) {
            let textContent = '';
            
            // 根据排版方向调整显示
            const isVertical = data.ocr_result.data.det_mode === 'sp';
            
            if (isVertical) {
                // 竖排文字，从右到左排列
                const linesArray = data.ocr_result.data.text_lines.map(line => line.text);
                // 按列排序
                linesArray.sort((a, b) => {
                    const posA = a.position ? a.position[0][0] : 0;
                    const posB = b.position ? b.position[0][0] : 0;
                    return posB - posA; // 从右到左
                });
                
                textContent = linesArray.join('\n');
            } else {
                // 横排文字，直接拼接
                data.ocr_result.data.text_lines.forEach(line => {
                    textContent += line.text + '\n';
                });
            }
            
            // 创建显示元素
            const textElement = document.createElement('pre');
            textElement.className = 'ocr-text';
            textElement.textContent = textContent;
            ocrResultBox.appendChild(textElement);
        }
        
        // 显示单字识别结果
        if (data.words_data && data.words_data.length > 0) {
            data.words_data.forEach(word => {
                const row = ocrTable.insertRow();
                
                // 图像单元格
                const imgCell = row.insertCell(0);
                const img = document.createElement('img');
                img.src = word.image;
                img.alt = word.text;
                img.addEventListener('click', function() {
                    modalImage.src = this.src;
                    imageModal.show();
                });
                imgCell.appendChild(img);
                
                // 文本单元格
                const textCell = row.insertCell(1);
                textCell.textContent = word.text;
                
                // 置信度单元格
                const confCell = row.insertCell(2);
                const confidence = Math.round(word.confidence * 100);
                confCell.textContent = `${confidence}%`;
                
                // 根据置信度设置颜色
                if (confidence >= 80) {
                    confCell.className = 'confidence-good';
                } else if (confidence >= 50) {
                    confCell.className = 'confidence-medium';
                } else {
                    confCell.className = 'confidence-bad';
                }
            });
        }
    }
    
    // 初始化函数
    function init() {
        // 初始化预处理选项状态
        if (preprocessToggle.checked) {
            document.querySelectorAll('.preprocess-option').forEach(option => option.disabled = false);
        } else {
            document.querySelectorAll('.preprocess-option').forEach(option => option.disabled = true);
        }
        
        // 加载设置
        fetch('/api/settings')
        .then(response => response.json())
        .then(settings => {
            // 填充设置表单
            document.getElementById('detModeSelect').value = settings.det_mode || 'sp';
            document.getElementById('imageSizeInput').value = settings.image_size || 1024;
            document.getElementById('versionSelect').value = settings.version || 'default';
            
            // 设置检测模式单选按钮
            const charOcr = settings.char_ocr !== undefined ? settings.char_ocr : true;
            document.getElementById(charOcr ? 'charDetRadio' : 'lineDetRadio').checked = true;
            
            // 设置预处理选项
            if (settings.preprocess !== undefined) {
                preprocessToggle.checked = settings.preprocess;
                if (settings.preprocess_options) {
                    document.getElementById('autoDeskewCheck').checked = 
                        settings.preprocess_options.auto_deskew !== undefined ? 
                        settings.preprocess_options.auto_deskew : true;
                    
                    document.getElementById('contrastCheck').checked = 
                        settings.preprocess_options.enhance_contrast !== undefined ? 
                        settings.preprocess_options.enhance_contrast : true;
                    
                    document.getElementById('noiseCheck').checked = 
                        settings.preprocess_options.noise_reduction !== undefined ? 
                        settings.preprocess_options.noise_reduction : true;
                    
                    document.getElementById('sharpenCheck').checked = 
                        settings.preprocess_options.sharpen !== undefined ? 
                        settings.preprocess_options.sharpen : true;
                }
                
                // 更新预处理选项可用状态
                if (preprocessToggle.checked) {
                    document.querySelectorAll('.preprocess-option').forEach(option => option.disabled = false);
                } else {
                    document.querySelectorAll('.preprocess-option').forEach(option => option.disabled = true);
                }
            }
            
            addLog('设置已加载');
        })
        .catch(error => {
            addLog(`加载设置异常: ${error.message}`, true);
        });
    }
    
    // 初始化应用
    init();
});
