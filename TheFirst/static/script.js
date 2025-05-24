// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // DOM元素缓存
    const elements = {
        selectFileBtn: document.getElementById('selectFileBtn'),
        imageInput: document.getElementById('imageInput'),
        previewImage: document.getElementById('previewImage'),
        executeOcrBtn: document.getElementById('executeOcrBtn'),
        zoomSlider: document.getElementById('zoomSlider'),
        zoomValue: document.getElementById('zoomValue'),
        logBox: document.getElementById('logBox'),
        ocrResultBox: document.getElementById('ocrResultBox'),
        ocrTableBody: document.getElementById('ocrTable').getElementsByTagName('tbody')[0],
        imageModal: new bootstrap.Modal(document.getElementById('imageModal')),
        modalImage: document.getElementById('modalImage'),
        useDefaultImgBtn: document.getElementById('useDefaultImgBtn'),
        uploadInfo: document.getElementById('uploadInfo'),
        selectedFileName: document.getElementById('selectedFileName'),
        processedImage: document.getElementById('processedImage'),
        noProcessedImage: document.getElementById('noProcessedImage'),
        convertToTraditionalBtn: document.getElementById('convertToTraditionalBtn'),
        convertToSimplifiedBtn: document.getElementById('convertToSimplifiedBtn'),
        preprocessToggle: document.getElementById('preprocessToggle'),
        preprocessOptions: document.getElementById('preprocessOptions'),
        historyList: document.getElementById('historyList'),
        noHistoryMsg: document.getElementById('noHistoryMsg'),
        historyImage: document.getElementById('historyImage'),
        noHistoryImageSelected: document.getElementById('noHistoryImageSelected'),
        historyText: document.getElementById('historyText'),
        noHistoryTextSelected: document.getElementById('noHistoryTextSelected'),
        downloadHistoryBtn: document.getElementById('downloadHistoryBtn'), 
        deleteHistoryBtn: document.getElementById('deleteHistoryBtn'),
        rotationSlider: document.getElementById('rotationSlider'),
        rotationValue: document.getElementById('rotationValue'),
        processTab: document.getElementById('process-tab'),
        uploadTab: document.getElementById('upload-tab'),
        resultTab: document.getElementById('result-tab'),
        processedZoomSlider: document.getElementById('processedZoomSlider'),
        processedZoomValue: document.getElementById('processedZoomValue'),
        processedRotationSlider: document.getElementById('processedRotationSlider'),
        processedRotationValue: document.getElementById('processedRotationValue'),
        // Assistant相关元素
        assistantChatHistory: document.getElementById('assistantChatHistory'),
        assistantQueryInput: document.getElementById('assistantQueryInput'),
        sendToAssistantBtn: document.getElementById('sendToAssistantBtn'),
        assistantStatus: document.getElementById('assistantStatus'),
        clearAssistantChatBtn: document.getElementById('clearAssistantChatBtn'),
        analyzeTextBtn: document.getElementById('analyzeTextBtn'),
        translateTextBtn: document.getElementById('translateTextBtn'),
        explainTextBtn: document.getElementById('explainTextBtn'),
        backgroundInfoBtn: document.getElementById('backgroundInfoBtn'),
    };

    // 变量
    let currentImagePath = null;
    let currentFullPath = null;
    let currentImageId = null;
    let currentScale = 1;
    let currentRotation = 0;
    let processedScale = 1;
    let processedRotation = 0;
    let originalOcrText = '';
    const defaultImagePath = 'TheFirst/static/images/placeholder.jpg';
    const default_image_path = 'static/images/placeholder.jpg';

    // --- 日志功能 ---
    function addLog(message, isError = false) {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry ' + (isError ? 'log-error' : '');
        logEntry.textContent = `[${timestamp}] ${message}`;
        elements.logBox.appendChild(logEntry);
        elements.logBox.scrollTop = elements.logBox.scrollHeight;
    }

    // --- OCR结果表格操作 ---
    function clearOcrTable() {
        elements.ocrTableBody.innerHTML = '';
    }
    
    // --- 图像操作 ---
    function resetImageTransform() {
        currentScale = 1;
        currentRotation = 0;
        processedScale = 1;
        processedRotation = 0;

        elements.zoomSlider.value = 100;
        elements.zoomValue.textContent = '100%';
        elements.rotationSlider.value = 0;
        elements.rotationValue.textContent = '0°';

        elements.processedZoomSlider.value = 100;
        elements.processedZoomValue.textContent = '100%';
        elements.processedRotationSlider.value = 0;
        elements.processedRotationValue.textContent = '0°';

        applyImageTransform();
        applyProcessedImageTransform();
    }

    function applyImageTransform() {
        elements.previewImage.style.transform = `rotate(${currentRotation}deg) scale(${currentScale})`;
        // 可选：添加动画效果
        elements.previewImage.style.transition = 'transform 0.2s ease';
    }

    function applyProcessedImageTransform() {
        elements.processedImage.style.transform = `rotate(${processedRotation}deg) scale(${processedScale})`;
        elements.processedImage.style.transition = 'transform 0.2s ease'; // 可选动画
    }

    // --- 事件监听器 ---
    elements.selectFileBtn.addEventListener('click', () => elements.imageInput.click());
    elements.imageInput.addEventListener('change', (event) => handleImageUpload(event.target.files[0]));
    elements.useDefaultImgBtn.addEventListener('click', handleDefaultImage);
    elements.executeOcrBtn.addEventListener('click', executeOcr);

    // 缩放滑块事件
    elements.zoomSlider.addEventListener('input', () => {
        currentScale = parseFloat(elements.zoomSlider.value) / 100;
        elements.zoomValue.textContent = `${elements.zoomSlider.value}%`;
        applyImageTransform();
    });

    // 旋转滑块事件
    elements.rotationSlider.addEventListener('input', () => {
        currentRotation = parseInt(elements.rotationSlider.value);
        elements.rotationValue.textContent = `${currentRotation}°`;
        applyImageTransform();
    });

    elements.processedZoomSlider.addEventListener('input', () => {
        processedScale = parseFloat(elements.processedZoomSlider.value) / 100;
        elements.processedZoomValue.textContent = `${elements.processedZoomSlider.value}%`;
        applyProcessedImageTransform();
    });

    elements.processedRotationSlider.addEventListener('input', () => {
        processedRotation = parseInt(elements.processedRotationSlider.value);
        elements.processedRotationValue.textContent = `${processedRotation}°`;
        applyProcessedImageTransform();
    });

    // --- History Record Download ---
function downloadHistoryRecord() {
    if (!currentImagePath || !currentImageId) {
        handleError('错误: 未选择要下载的历史记录');
        return;
    }

    addLog(`准备下载历史记录 #${currentImageId}`);

    // 下载图像
    let imageName;
    try {
        const urlParts = currentImagePath.split('/');
        const originalFileName = urlParts[urlParts.length - 1];
        const extension = originalFileName.substring(originalFileName.lastIndexOf('.'));
        imageName = `历史图像_${currentImageId}${extension}`;
    } catch (e) {
        imageName = `历史图像_${currentImageId}.jpg`; // Fallback name
    }

    const imageLink = document.createElement('a');
    imageLink.href = currentImagePath;
    imageLink.download = imageName;
    document.body.appendChild(imageLink);
    imageLink.click();
    document.body.removeChild(imageLink);
    addLog(`图像 ${imageName} 开始下载...`);

    // 下载文本
    const ocrText = elements.historyText.textContent;
    if (ocrText && ocrText.trim() !== '' && ocrText.trim() !== elements.noHistoryTextSelected.textContent.trim()) {
        const textBlob = new Blob([ocrText], { type: 'text/plain;charset=utf-8' });
        const textUrl = URL.createObjectURL(textBlob);
        const textName = `历史文本_${currentImageId}.txt`;
        const textLink = document.createElement('a');
        textLink.href = textUrl;
        textLink.download = textName;
        document.body.appendChild(textLink);
        textLink.click();
        document.body.removeChild(textLink);
        URL.revokeObjectURL(textUrl); 
        addLog(`文本文件 ${textName} 开始下载...`);
    } else {
        addLog('没有关联的OCR文本可供下载。');
    }
}

    // --- 文件操作 ---
    function handleImageUpload(file) {
        if (!file) return;

        showLoadingIndicator();
        addLog(`选择文件: ${file.name}`);
        updateFileInfoDisplay(file.name);

        const formData = new FormData();
        formData.append('image', file);

        fetch('/api/upload', {
            method: 'POST',
            body: formData
        })
        .then(checkResponseStatus)
        .then(response => response.json())
        .then(data => {
            hideLoadingIndicator();
            if (data.error) {
                handleError(`上传错误: ${data.error}`);
                return;
            }
            updateImageDisplay(data.image_path, data.full_path, data.image_id);
            resetImageTransform();
            enableOcrButton();
            switchToProcessTab();
        })
        .catch(handleFetchError);
    }

    function updateFileInfoDisplay(fileName) {
        elements.uploadInfo.style.display = 'block';
        elements.selectedFileName.textContent = fileName;
    }

    function updateImageDisplay(imagePath, fullPath, imageId) {
        currentImagePath = imagePath;
        currentFullPath = fullPath;
        currentImageId = imageId;
        elements.previewImage.src = imagePath;
        addLog(`文件上传成功: ${imagePath}`);
    }

    function handleDefaultImage() {
        showLoadingIndicator();
        addLog('使用默认样例图像');
        updateFileInfoDisplay('默认样例图像');
        updateImageDisplay(default_image_path, defaultImagePath, 'default_sample');
        resetImageTransform();
        enableOcrButton();
        switchToProcessTab();
        hideLoadingIndicator(500);
    }

    // --- OCR操作 ---
    function executeOcr() {
        if (!currentImagePath) {
            handleError('错误: 未选择图像文件');
            return;
        }

        const ocrParams = gatherOcrParams();
        logOcrParameters(ocrParams);
        showLoadingIndicator();

        let ocrPromise;
        if (ocrParams.version === 'baidu') {
            ocrPromise = fetch('/api/baidu_ocr', createFetchOptions('POST', ocrParams));
        } else {
            ocrPromise = fetch('/api/ocr', createFetchOptions('POST', ocrParams));
        }

        ocrPromise
        .then(checkResponseStatus)
        .then(response => response.json())
        .then(data => {
            hideLoadingIndicator();
            if (data.error) {
                handleError(`OCR处理错误: ${data.error}`);
                return;
            }
            processOcrResult(data);
            addLog('OCR处理完成');
            switchToResultTab();
            fetchHistory(); // 更新历史记录
        })
        .catch(handleFetchError);
    }

    function gatherOcrParams() {
        return {
            image_path: currentImagePath,
            full_path: currentFullPath,
            image_id: currentImageId,
            det_mode: document.getElementById('detModeSelect').value,
            char_ocr: document.querySelector('input[name="detMode"]:checked').value === 'true',
            image_size: parseInt(document.getElementById('imageSizeInput').value),
            version: document.getElementById('versionSelect').value,
            preprocess: elements.preprocessToggle.checked,
            preprocess_options: gatherPreprocessOptions(),
            is_default_image: currentImagePath === defaultImagePath
        };
    }

    function gatherPreprocessOptions() {
        return {
            auto_deskew: elements.preprocessToggle.checked && document.getElementById('autoDeskewCheck').checked,
            enhance_contrast: elements.preprocessToggle.checked && document.getElementById('contrastCheck').checked,
            noise_reduction: elements.preprocessToggle.checked && document.getElementById('noiseCheck').checked,
            sharpen: elements.preprocessToggle.checked && document.getElementById('sharpenCheck').checked,
            binarize: elements.preprocessToggle.checked && document.getElementById('binarizeCheck').checked
        };
    }

    function logOcrParameters(params) {
        let versionText = '';
        switch (params.version) {
            case 'default': versionText = '标准版本'; break;
            case 'beta': versionText = '语序优化版本'; break;
            case 'baidu': versionText = '百度OCR'; break;
        }
        const detModeText = params.det_mode === 'sp' ? '竖排' : (params.det_mode === 'hp' ? '横排' : '自动');
        const detTypeText = params.char_ocr ? '单字检测识别' : '文本行检测识别';

        addLog(`识别参数信息:`);
        addLog(`- 识别版本: ${versionText}`);
        addLog(`- 文字排版方向: ${detModeText}`);
        addLog(`- 检测模式: ${detTypeText}`);
        addLog(`- 图片尺寸: ${params.image_size}px`);
        addLog(`- 图像预处理: ${params.preprocess ? '开启' : '关闭'}`);

        if (params.preprocess) {
            const preOptions = params.preprocess_options;
            addLog(`  - 自动校正倾斜: ${preOptions.auto_deskew ? '是' : '否'}`);
            addLog(`  - 增强对比度: ${preOptions.enhance_contrast ? '是' : '否'}`);
            addLog(`  - 降噪处理: ${preOptions.noise_reduction ? '是' : '否'}`);
            addLog(`  - 锐化处理: ${preOptions.sharpen ? '是' : '否'}`);
            addLog(`  - 二值化处理: ${preOptions.binarize ? '是' : '否'}`);
        }
    }

    function processOcrResult(data) {
        updateProcessedImageView(data.processed_image);
        displayOcrText(data.ocr_result);
        displayWordDetails(data.words_data);
    }

    function updateProcessedImageView(processedImagePath) {
        if (processedImagePath) {
            elements.processedImage.src = processedImagePath;
            elements.processedImage.style.display = 'block';
            elements.noProcessedImage.style.display = 'none';
        } else {
            elements.processedImage.style.display = 'none';
            elements.noProcessedImage.style.display = 'block';
        }
    }

    function displayOcrText(ocrResult) {
        elements.ocrResultBox.innerHTML = '';
        clearOcrTable();
        originalOcrText = '';

        if (ocrResult && ocrResult.data && ocrResult.data.text_lines && ocrResult.data.text_lines.length > 0) {
            const linesArray = ocrResult.data.text_lines.map(line => line.text);
            originalOcrText = linesArray.join('\n');
            const isVertical = (ocrResult.data.det_mode === 'sp') || (document.getElementById('detModeSelect').value === 'sp' && ocrResult.data.det_mode === 'auto');
            const textContent = isVertical ? originalOcrText : originalOcrText;
            createTextElement(textContent);
            showConversionButtons();
        } else {
            hideConversionButtons();
            addLog('OCR未能识别出文本内容。');
        }
    }

    function createTextElement(textContent) {
        const textElement = document.createElement('pre');
        textElement.className = 'ocr-text';
        textElement.textContent = textContent.trim();
        elements.ocrResultBox.appendChild(textElement);
    }

    function displayWordDetails(wordsData) {
        if (wordsData && wordsData.length > 0) {
            wordsData.forEach(word => {
                const row = elements.ocrTableBody.insertRow();

                const imgCell = row.insertCell(0);
                const img = createImageElement(word);
                imgCell.appendChild(img);

                const textCell = row.insertCell(1);
                textCell.textContent = word.text;

                const confCell = row.insertCell(2);
                const confidence = Math.round(word.confidence * 100);
                confCell.textContent = `${confidence}%`;
                confCell.className = getConfidenceClass(confidence);
            });
        }
    }

    function createImageElement(word) {
        const img = document.createElement('img');
        img.src = word.image;
        img.alt = word.text;
        img.className = 'char-image';
        img.addEventListener('click', () => showModalImage(img.src));
        return img;
    }

    function getConfidenceClass(confidence) {
        if (confidence >= 80) return 'confidence-good';
        if (confidence >= 50) return 'confidence-medium';
        return 'confidence-bad';
    }

    function showModalImage(src) {
        elements.modalImage.src = src;
        elements.imageModal.show();
    }

    // --- 文本转换操作 ---
    function convertText(conversionType) {
        if (!originalOcrText) {
            handleError('没有可供转换的原始OCR文本。');
            return;
        }

        showLoadingIndicator(elements.ocrResultBox.parentNode);
        addLog(`正在将文本转换为 ${conversionType === 's2t' ? '繁体' : '简体'}...`);

        fetch('/api/convert_text', createFetchOptions('POST', { text: originalOcrText, type: conversionType }))
        .then(checkResponseStatus)
        .then(response => response.json())
        .then(data => {
            hideLoadingIndicator();
            if (data.error) {
                handleError(`文本转换错误: ${data.error}`);
                return;
            }
            updateTextDisplay(data.converted_text, conversionType);
            addLog(`文本已成功转换为 ${conversionType === 's2t' ? '繁体' : '简体'}`);
        })
        .catch(handleFetchError);
    }

    function updateTextDisplay(convertedText, conversionType) {
        const textElement = elements.ocrResultBox.querySelector('.ocr-text') || document.createElement('pre');
        textElement.className = 'ocr-text';
        textElement.textContent = convertedText.trim();
        if (!elements.ocrResultBox.querySelector('.ocr-text')) {
            elements.ocrResultBox.innerHTML = '';
            elements.ocrResultBox.appendChild(textElement);
        }
        setActiveConversionButton(conversionType);
    }

    function setActiveConversionButton(conversionType) {
        elements.convertToTraditionalBtn.classList.toggle('active', conversionType === 's2t');
        elements.convertToSimplifiedBtn.classList.toggle('active', conversionType === 't2s');
    }

    function showConversionButtons() {
        if (elements.convertToTraditionalBtn && elements.convertToSimplifiedBtn) {
            elements.convertToTraditionalBtn.style.display = 'inline-block';
            elements.convertToSimplifiedBtn.style.display = 'inline-block';
        }
    }

    function hideConversionButtons() {
        if (elements.convertToTraditionalBtn && elements.convertToSimplifiedBtn) {
            elements.convertToTraditionalBtn.style.display = 'none';
        }
    }

    // --- 历史记录操作 ---
    function fetchHistory() {
        fetch('/api/history')
        .then(checkResponseStatus)
        .then(response => response.json())
        .then(displayHistory)
        .catch(handleFetchError);
    }

    function displayHistory(history) {
        elements.historyList.innerHTML = '';
        if (history && history.length > 0) {
            elements.noHistoryMsg.style.display = 'none';
            history.forEach(record => {
                const item = createHistoryItem(record);
                elements.historyList.appendChild(item);
            });
        } else {
            elements.noHistoryMsg.style.display = 'block';
        }
    }

    function createHistoryItem(record) {
        const item = document.createElement('a');
        item.className = 'list-group-item list-group-item-action history-item';
        item.textContent = `记录 #${record.id} - ${record.timestamp}`;
        item.addEventListener('click', () => showHistoryDetail(record.id));
        return item;
    }

    function showHistoryDetail(recordId) {
        fetch(`/api/history/${recordId}`).then(checkResponseStatus)
        .then(response => response.json())
        .then(record => {
            if (record) {
                displayHistoryDetail(record);
            } else {
                handleError('未找到历史记录详情');
            }
        })
        .catch(handleFetchError);
    }

    function displayHistoryDetail(record) {
        currentImagePath = record.image_path;
        currentFullPath = record.image_path; 
        currentImageId = record.id;

        elements.historyImage.src = record.image_path;
        elements.historyText.textContent = record.ocr_text;
        elements.historyImage.style.display = 'block';
        elements.historyText.style.display = 'block';
        elements.noHistoryImageSelected.style.display = 'none';
        elements.noHistoryTextSelected.style.display = 'none';
        elements.downloadHistoryBtn.style.display = 'inline-block'; 
        elements.deleteHistoryBtn.style.display = 'inline-block';
    }


    function deleteSelectedHistoryRecord() {
        if (!confirm('确定要删除此历史记录吗？')) return;

        if (currentImageId) {
            fetch(`/api/history/delete/${currentImageId}`, createFetchOptions('DELETE'))
            .then(checkResponseStatus)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    addLog(data.message);
                    clearHistoryDetailDisplay();
                    fetchHistory();
                } else {
                    handleError(`删除历史记录失败: ${data.error}`);
                }
            })
            .catch(handleFetchError);
        } else {
            handleError('未选择要删除的历史记录');
        }
    }

    function clearHistoryDetailDisplay() {
        elements.historyImage.src = '';
        elements.historyText.textContent = '';
        elements.historyImage.style.display = 'none';
        elements.historyText.style.display = 'none';
        elements.noHistoryImageSelected.style.display = 'block';
        elements.noHistoryTextSelected.style.display = 'block';
        elements.downloadHistoryBtn.style.display = 'none'; 
        elements.deleteHistoryBtn.style.display = 'none';
    }

    // --- 界面控制 ---
    function enableOcrButton() {
        elements.executeOcrBtn.disabled = false;
    }

    function disableOcrButton() {
        elements.executeOcrBtn.disabled = true;
    }

    function switchToProcessTab() {
        if (elements.processTab && elements.uploadTab) {
            const processTab = new bootstrap.Tab(elements.processTab);
            processTab.show();
        }
    }

    function switchToUploadTab() {
        if (elements.processTab && elements.uploadTab) {
            const uploadTab = new bootstrap.Tab(elements.uploadTab);
            uploadTab.show();
        }
    }

    function switchToResultTab() {
        if (elements.resultTab) {
            const resultTab = new bootstrap.Tab(elements.resultTab);
            resultTab.show();
        }
    }

    // --- 加载指示器 ---
    function showLoadingIndicator(target = document.getElementById('imageContainer')) {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'loading';
        target.appendChild(loadingDiv);
        disableOcrButton();
    }

    function hideLoadingIndicator(delay = 0) {
        setTimeout(() => {
            const loadingDiv = document.querySelector('.loading');
            if (loadingDiv) {
                loadingDiv.remove();
            }
            enableOcrButton();
        }, delay);
    }

    // --- 错误处理 ---
    function handleError(message) {
        addLog(`错误: ${message}`, true);
        hideLoadingIndicator();
    }

    function handleFetchError(error) {
        console.error('Fetch error:', error);
        handleError(`网络请求错误: ${error.message || '未知错误'}`);
    }

    function checkResponseStatus(response) {
        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`);
        }
        return response;
    }

    function createFetchOptions(method, body = null) {
        const options = {
            method: method,
            headers: { 'Content-Type': 'application/json' }
        };
        if (body) {
            options.body = JSON.stringify(body);
        }
        return options;
    }

    // --- 事件监听器 ---
    elements.imageInput.addEventListener('change', (event) => handleImageUpload(event.target.files[0]));
    elements.useDefaultImgBtn.addEventListener('click', handleDefaultImage);
    elements.executeOcrBtn.addEventListener('click', executeOcr);
    elements.zoomSlider.addEventListener('input', () => {
        currentScale = elements.zoomSlider.value / 100;
        elements.zoomValue.textContent = `${elements.zoomSlider.value}%`;
        updateImageTransform();
    });
    elements.rotationSlider.addEventListener('input', () => {
        currentRotation = elements.rotationSlider.value;
        elements.rotationValue.textContent = `${elements.rotationSlider.value}°`;
        updateImageTransform();
    });
    elements.convertToTraditionalBtn.addEventListener('click', () => convertText('s2t'));
    elements.convertToSimplifiedBtn.addEventListener('click', () => convertText('t2s'));
    elements.preprocessToggle.addEventListener('change', () => {
        const disabled = !elements.preprocessToggle.checked;
        document.querySelectorAll('.preprocess-option').forEach(option => option.disabled = disabled);
    });
    // elements.useHistoryImageBtn.addEventListener('click', useSelectedHistoryImage);
    elements.deleteHistoryBtn.addEventListener('click', deleteSelectedHistoryRecord);
    elements.downloadHistoryBtn.addEventListener('click', downloadHistoryRecord);

    // --- 初始化 ---
    function init() {
        initSettingsForm();
        initPreprocessOptions();
        resetImageTransform();
        fetchHistory();
    }

    function initSettingsForm() {
        fetch('/api/settings')
        .then(checkResponseStatus)
        .then(response => response.json())
        .then(settings => {
            document.getElementById('detModeSelect').value = settings.det_mode || 'sp';
            document.getElementById('imageSizeInput').value = settings.image_size || 1024;
            document.getElementById('versionSelect').value = settings.version || 'default';
            document.getElementById(settings.char_ocr ? 'charDetRadio' : 'lineDetRadio').checked = true;
            initPreprocessSettings(settings);
        })
        .catch(handleFetchError);
    }

    function initPreprocessSettings(settings) {
        elements.preprocessToggle.checked = settings.preprocess !== undefined ? settings.preprocess : true;
        const disabled = !elements.preprocessToggle.checked;
        document.querySelectorAll('.preprocess-option').forEach(option => option.disabled = disabled);

        if (settings.preprocess_options) {
            document.getElementById('autoDeskewCheck').checked = settings.preprocess_options.auto_deskew !== undefined ? settings.preprocess_options.auto_deskew : false;
            document.getElementById('contrastCheck').checked = settings.preprocess_options.enhance_contrast !== undefined ? settings.preprocess_options.enhance_contrast : false;
            document.getElementById('noiseCheck').checked = settings.preprocess_options.noise_reduction !== undefined ? settings.preprocess_options.noise_reduction : false;
            document.getElementById('sharpenCheck').checked = settings.preprocess_options.sharpen !== undefined ? settings.preprocess_options.sharpen : false;
            document.getElementById('binarizeCheck').checked = settings.preprocess_options.binarize !== undefined ? settings.preprocess_options.binarize : false;
        }
    }

    function initPreprocessOptions() {
        const disabled = !elements.preprocessToggle.checked;
        document.querySelectorAll('.preprocess-option').forEach(option => option.disabled = disabled);
    }

    // === DeepSeek 助手相关变量 ===
    // 聊天记录缓存
    let assistantChatHistory = [];

    function sendMessageToAssistant(message, context = '') {
        if (!message.trim()) {
            handleError('请输入您的问题或需求');
            return;
        }

        const userEntry = { role: 'user', content: message };
        assistantChatHistory.push(userEntry);
        updateAssistantChatUI();

        elements.assistantStatus.textContent = '正在分析中，请稍候...';

        fetch('/api/assistant/chat', createFetchOptions('POST', {
            message: message,
            context_text: context,
            conversation_history: assistantChatHistory
        }))
        .then(checkResponseStatus)
        .then(response => response.json())
        .then(data => {
            elements.assistantStatus.textContent = '';
            if (data.error) {
                handleError(`智能助手响应异常: ${data.error}`);
                return;
            }

            const assistantReply = { role: 'assistant', content: data.reply };
            assistantChatHistory.push(assistantReply);
            updateAssistantChatUI();
        })
        .catch(error => {
            elements.assistantStatus.textContent = '';
            handleFetchError(error);
        });
    }

    function updateAssistantChatUI() {
        elements.assistantChatHistory.innerHTML = '';
        assistantChatHistory.forEach(entry => {
            const msgDiv = document.createElement('div');
            msgDiv.className = entry.role === 'user' ? 'chat-message user' : 'chat-message assistant';
            msgDiv.textContent = entry.content;
            elements.assistantChatHistory.appendChild(msgDiv);
        });
        elements.assistantChatHistory.scrollTop = elements.assistantChatHistory.scrollHeight;
    }

    // 发送按钮事件
    elements.sendToAssistantBtn.addEventListener('click', () => {
        const msg = elements.assistantQueryInput.value;
        sendMessageToAssistant(msg, originalOcrText);
        elements.assistantQueryInput.value = '';
    });

    // 回车发送
    elements.assistantQueryInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            elements.sendToAssistantBtn.click();
        }
    });

    // 清空对话历史
    elements.clearAssistantChatBtn.addEventListener('click', () => {
        if (assistantChatHistory.length > 0) {
            if (confirm('确定要清空所有对话记录吗？')) {
                assistantChatHistory = [];
                updateAssistantChatUI();
                elements.assistantStatus.textContent = '';
            }
        }
    });

    // 功能按钮：分析、翻译、解释、背景
    elements.analyzeTextBtn.addEventListener('click', () => {
        sendMessageToAssistant('请分析这段古文的结构与用词。', originalOcrText);
    });

    elements.translateTextBtn.addEventListener('click', () => {
        sendMessageToAssistant('请翻译这段古文为现代汉语。', originalOcrText);
    });

    elements.explainTextBtn.addEventListener('click', () => {
        sendMessageToAssistant('请逐句解释这段古文的意思。', originalOcrText);
    });

    elements.backgroundInfoBtn.addEventListener('click', () => {
        sendMessageToAssistant('请提供这段古文的背景信息或出处。', originalOcrText);
    });
    
    // // 文本分析功能
    // elements.analyzeTextBtn.addEventListener('click', () => {
    //     const prompt = `请对以下古文进行深入分析：

    // 1. 文体特征：判断文体类型（如散文、骈文、诗歌等）
    // 2. 语言特色：分析用词、句式、修辞手法
    // 3. 结构层次：梳理文章脉络和逻辑结构
    // 4. 艺术特色：评析文学价值和艺术手法

    // 请提供专业而易懂的分析。`;
        
    //     sendMessageToAssistant(prompt, originalOcrText);
    // });

    // // 翻译功能
    // elements.translateTextBtn.addEventListener('click', () => {
    //     const prompt = `请将以下古文翻译为现代汉语：

    // 翻译要求：
    // 1. 准确传达原文意思，不遗漏要点
    // 2. 语言流畅自然，符合现代汉语表达习惯
    // 3. 保持原文的语气和风格特色
    // 4. 对于关键词汇，请在译文后用括号标注原文

    // 请提供完整的现代汉语译文。`;
        
    //     sendMessageToAssistant(prompt, originalOcrText);
    // });

    // // 逐句解释功能
    // elements.explainTextBtn.addEventListener('click', () => {
    //     const prompt = `请对以下古文进行逐句详细解释：

    // 解释内容包括：
    // 1. 句子结构分析（主谓宾、定状补等）
    // 2. 重点词汇释义（古今异义、一词多义等）
    // 3. 语法现象说明（倒装、省略、活用等）
    // 4. 句意理解和现代汉语表达

    // 请按原文顺序，逐句进行详尽解释。`;
        
    //     sendMessageToAssistant(prompt, originalOcrText);
    // });

    // // 背景信息功能
    // elements.backgroundInfoBtn.addEventListener('click', () => {
    //     const prompt = `请提供以下古文的相关背景信息：

    // 背景信息包括：
    // 1. 作者简介：生平、地位、代表作品
    // 2. 创作背景：写作时间、历史背景、创作缘由
    // 3. 文献出处：出自哪部典籍或文集
    // 4. 历史价值：在文学史上的地位和影响
    // 5. 相关典故：涉及的历史事件、人物、典故

    // 如无法确定具体出处，请说明可能的来源和相关信息。`;
        
    //     sendMessageToAssistant(prompt, originalOcrText);
    // });


    init();
});
