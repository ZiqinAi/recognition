# preprocess.py - 图像预处理
import cv2
import os
from PIL import Image
import numpy as np

PREPROCESS_FOLDER = 'TheFirst/static/preprocessed'

class ImagePreprocessor:
    @staticmethod
    def preprocess_image(image_path, image_id, preprocess_options):
        """
        预处理图像以提高OCR准确性

        参数:
        - image_path: 原始图像路径
        - image_id: 图像ID，用于创建独立的预处理结果文件夹
        - preprocess_options: 包含预处理选项的字典，键包括:
            - auto_deskew: bool, 是否自动校正图像倾斜
            - enhance_contrast: bool, 是否增强图像对比度
            - reduce_noise: bool, 是否减少图像噪点
            - sharpen: bool, 是否锐化图像
            - binarize: bool, 是否二值化处理

        返回:
        - 一个包含预处理结果的字典:
            - status: 'success' 或 'error'
            - preprocessed_image_path: str, 预处理后的彩色/主要图像的Web路径 (如果成功)
            - preprocessed_gray_path: str, 预处理后的灰度图像的Web路径 (如果成功)
            - local_path: str, 预处理后的彩色/主要图像在服务器上的本地文件系统路径 (如果成功)
            - preprocessed_binary_path: str, (可选) 二值化图像的Web路径 (如果启用了二值化且成功)
            - error: str, 错误信息 (如果status为'error')
        """
        try:
            # --- 1. 初始化与图像加载 ---
            # 尝试使用OpenCV读取图像
            cv_image = cv2.imread(image_path)
            if cv_image is None:
                # 如果OpenCV无法读取 (可能是不常见的格式或路径问题), 尝试使用Pillow (PIL) 读取
                pil_image = Image.open(image_path)
                # 将Pillow图像对象转换为NumPy数组，这是OpenCV处理图像的格式
                cv_image = np.array(pil_image)
                # Pillow读取的RGB图像需要转换为OpenCV默认的BGR格式
                if len(cv_image.shape) == 3 and cv_image.shape[2] == 3: # 检查是否为三通道彩色图像
                    cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)

            # 为当前图像的预处理结果创建一个唯一的文件夹，路径为 PREPROCESS_FOLDER/image_id
            preprocess_dir = os.path.join(PREPROCESS_FOLDER, str(image_id))
            os.makedirs(preprocess_dir, exist_ok=True) # exist_ok=True 表示如果文件夹已存在则不报错

            # 将图像转换为灰度图，许多预处理操作在灰度图上更有效或定义更清晰
            # 如果原图是三通道 (彩色), 则转为灰度; 如果已经是单通道 (灰度), 则复制一份使用
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY) if len(cv_image.shape) == 3 else cv_image.copy()

            # 记录原始灰度图像的清晰度 (拉普拉斯方差可衡量图像的边缘数量和强度)
            # 这个值后续可用于智能锐化等步骤，判断处理是否导致图像模糊
            original_variance = cv2.Laplacian(gray, cv2.CV_64F).var()

            # --- 2. 根据 preprocess_options 执行选定的预处理步骤 ---

            # 步骤 2.1: 自动校正倾斜
            # 默认关闭 (False), 因为不当的倾斜校正可能反而降低图像质量
            if preprocess_options.get('auto_deskew', False):
                # 对灰度图像进行倾斜校正
                gray = ImagePreprocessor._deskew(gray)

            # 步骤 2.2: 增强对比度
            # 默认开启 (True), 通常能改善文本和背景的区分度
            if preprocess_options.get('enhance_contrast', True):
                # 对灰度图像进行对比度增强
                gray = ImagePreprocessor._enhance_contrast(gray)

            # 步骤 2.3: 智能降噪
            # 默认关闭 (False), 因为降噪可能导致图像细节丢失
            if preprocess_options.get('reduce_noise', False):
                # 首先检测图像是否真的存在明显噪点
                if ImagePreprocessor._has_noise(gray):
                    # 如果检测到噪点，则对灰度图像进行降噪处理
                    gray = ImagePreprocessor._reduce_noise(gray)

            # 步骤 2.4: 智能锐化
            # 默认关闭 (False), 过度锐化可能产生伪影
            if preprocess_options.get('sharpen', False):
                # 计算当前处理后灰度图像的清晰度
                current_variance = cv2.Laplacian(gray, cv2.CV_64F).var()
                # 只有当图像清晰度显著低于原始清晰度时 (例如，因其他处理导致模糊), 才进行锐化
                if current_variance < original_variance * 0.8:
                    gray = ImagePreprocessor._smart_sharpen(gray)

            # 步骤 2.5: 二值化处理
            # 默认开启 (True), 对于许多OCR引擎，清晰的二值图像效果最好
            if preprocess_options.get('binarize', True):
                # 对灰度图像进行自适应二值化
                binary = ImagePreprocessor._adaptive_binarize(gray)
                # 保存二值化后的图像到预处理文件夹
                binary_path = os.path.join(preprocess_dir, "preprocessed_binary.png")
                cv2.imwrite(binary_path, binary)

            # --- 3. 保存预处理后的灰度图像和最终的（可能彩色的）图像 ---

            # 保存经过上述所有选定步骤处理后的灰度图像
            processed_gray_path = os.path.join(preprocess_dir, "preprocessed_gray.png")
            cv2.imwrite(processed_gray_path, gray)

            # 处理最终输出的图像 (可能是彩色的)
            # 如果原始图像是彩色的 (三通道)
            if len(cv_image.shape) == 3:
                # 针对原始彩色图像应用一些类似但可能更温和的变换
                # (注意: 这里并没有对 cv_image 应用上面灰度图的所有变换，仅包括倾斜校正和对比度增强)
                # 彩色图像的倾斜校正
                if preprocess_options.get('auto_deskew', False):
                    cv_image = ImagePreprocessor._deskew_color(cv_image)
                # 彩色图像的对比度增强
                if preprocess_options.get('enhance_contrast', True):
                    cv_image = ImagePreprocessor._enhance_contrast_color(cv_image)
            else:
                # 如果原始图像是灰度的，则将最终处理过的灰度图转换为BGR三通道格式作为输出
                # 这是为了保持输出图像格式的一致性 (多数情况下期望三通道图像)
                cv_image = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

            # 保存最终处理后的（可能是彩色的）图像
            processed_image_path_local = os.path.join(preprocess_dir, "preprocessed.png")
            cv2.imwrite(processed_image_path_local, cv_image)

            # --- 4. 构建并返回结果字典 ---
            result = {
                'status': 'success',
                # Web路径用于前端显示图像
                'preprocessed_image_path': f"/static/preprocessed/{image_id}/preprocessed.png",
                'preprocessed_gray_path': f"/static/preprocessed/{image_id}/preprocessed_gray.png",
                # 本地文件系统路径，可能用于后端进一步处理，如OCR
                'local_path': processed_image_path_local
            }

            # 如果进行了二值化处理，也在结果中添加二值化图像的Web路径
            if preprocess_options.get('binarize', True):
                result['preprocessed_binary_path'] = f"/static/preprocessed/{image_id}/preprocessed_binary.png"

            return result

        except Exception as e:
            # 如果在预处理过程中发生任何异常，捕获错误并返回错误信息
            return {
                'status': 'error',
                'error': str(e)
            }

    @staticmethod
    def _has_noise(image):
        """
        检测图像是否有明显噪声。
        原理: 噪声通常表现为像素值的快速、小范围波动。
              通过比较原图与轻微平滑（高斯模糊）后的图像的差异，可以量化这种波动。
              如果平均差异较大，则认为存在明显噪点。
        """
        try:
            # 使用3x3的高斯核进行轻微模糊
            blurred = cv2.GaussianBlur(image, (3, 3), 0)
            # 计算原图与模糊图像之间的绝对差值
            diff = cv2.absdiff(image, blurred)
            # 计算差值图像的平均强度，作为噪声水平的估计
            noise_level = np.mean(diff)

            # 如果噪声水平超过预设阈值5 (经验值)，则认为图像有明显噪声
            return noise_level > 5
        except:
            # 如果在检测过程中发生错误，保守地认为没有噪声
            return False

    @staticmethod
    def _deskew(image):
        """
        对灰度图像进行更精确的倾斜校正。
        原理: 基于主成分分析 (PCA) 找到图像中主要内容（非背景像素）的分布方向。
              这个方向被认为是文本行或主要特征的方向。然后计算该方向与水平方向的夹角，
              并旋转图像以校正这个角度。
        """
        try:
            # 找到图像中所有非纯黑(>0)像素的坐标。这些点被认为是前景内容。
            coords = np.column_stack(np.where(image > 0))
            # 如果前景点过少 (少于100个)，可能无法准确判断倾斜，直接返回原图
            if len(coords) < 100:
                return image

            # 计算这些坐标点的均值，并将坐标中心化 (减去均值)
            mean = np.mean(coords, axis=0)
            coords_centered = coords - mean

            # 计算中心化后坐标的协方差矩阵
            cov_matrix = np.cov(coords_centered.T)
            # 计算协方差矩阵的特征值和特征向量
            # 特征向量对应数据分布的主轴方向，最大特征值对应的特征向量是数据方差最大的方向。
            eigenvalues, eigenvectors = np.linalg.eig(cov_matrix)

            # 获取主方向 (最大特征值对应的特征向量)
            main_direction = eigenvectors[:, np.argmax(eigenvalues)]
            # 计算主方向与x轴的夹角 (弧度)
            angle = np.arctan2(main_direction[1], main_direction[0])
            angle_degrees = np.degrees(angle) # 转换为角度

            # 将角度标准化到 -45 到 +45 度之间，以便进行校正
            # 因为文本通常是水平或接近水平的，较大的角度可能是由于主方向检测的歧义性
            if angle_degrees > 45:
                angle_degrees -= 90
            elif angle_degrees < -45:
                angle_degrees += 90

            # 只有当检测到的倾斜角度绝对值大于2.0度时，才执行旋转操作
            # 这是一个阈值，避免对微小倾斜或噪声导致的误判进行不必要的旋转
            if abs(angle_degrees) > 2.0:
                (h, w) = image.shape[:2] # 获取图像高度和宽度
                center = (w // 2, h // 2) # 计算图像中心点

                # 获取旋转矩阵。围绕中心点旋转 -angle_degrees (因为我们想反向旋转以校正)
                # 缩放因子为1.0，即不缩放
                M = cv2.getRotationMatrix2D(center, -angle_degrees, 1.0)

                # 计算旋转后图像的新边界框大小，以确保整个原图像内容都可见，不被裁剪
                cos = np.abs(M[0, 0])
                sin = np.abs(M[0, 1])
                new_w = int((h * sin) + (w * cos))
                new_h = int((h * cos) + (w * sin))

                # 调整旋转矩阵的平移分量，以确保旋转后的图像在新画布的中心
                M[0, 2] += (new_w / 2) - center[0]
                M[1, 2] += (new_h / 2) - center[1]

                # 执行仿射变换 (旋转)
                # flags=cv2.INTER_LANCZOS4: 使用Lanczos插值，这是一种高质量的插值方法，能较好保留细节
                # borderMode=cv2.BORDER_CONSTANT: 边界填充模式为常量
                # borderValue=255: 填充颜色为白色 (255)，适用于文本图像
                rotated = cv2.warpAffine(image, M, (new_w, new_h),
                                      flags=cv2.INTER_LANCZOS4,
                                      borderMode=cv2.BORDER_CONSTANT,
                                      borderValue=255)
                return rotated

            # 如果倾斜角度不大于阈值，则返回原始图像
            return image

        except Exception:
            # 如果在倾斜校正过程中发生任何错误，则返回原始图像，避免程序崩溃
            return image

    @staticmethod
    def _deskew_color(image):
        """
        对彩色图像进行倾斜校正。
        原理: 与灰度图类似，但首先将彩色图转为灰度以检测倾斜角度，
              然后将检测到的角度应用于原始彩色图像的旋转。
              检测前景时使用 < 200 (非接近纯白) 的像素。
        """
        try:
            # 将彩色图像转换为灰度图像，用于倾斜检测
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # 找到灰度图像中非白色区域 (像素值 < 200) 的坐标
            coords = np.column_stack(np.where(gray < 200))
            if len(coords) < 100: # 前景点太少，不进行校正
                return image

            # 后续步骤与灰度图的 _deskew 方法中的 PCA 分析和角度计算相同
            mean = np.mean(coords, axis=0)
            coords_centered = coords - mean

            cov_matrix = np.cov(coords_centered.T)
            eigenvalues, eigenvectors = np.linalg.eig(cov_matrix)

            main_direction = eigenvectors[:, np.argmax(eigenvalues)]
            angle = np.arctan2(main_direction[1], main_direction[0])
            angle_degrees = np.degrees(angle)

            if angle_degrees > 45:
                angle_degrees -= 90
            elif angle_degrees < -45:
                angle_degrees += 90

            if abs(angle_degrees) > 2.0: # 仅当倾斜角度明显时才校正
                (h, w) = image.shape[:2]
                center = (w // 2, h // 2)

                M = cv2.getRotationMatrix2D(center, -angle_degrees, 1.0)

                cos = np.abs(M[0, 0])
                sin = np.abs(M[0, 1])
                new_w = int((h * sin) + (w * cos))
                new_h = int((h * cos) + (w * sin))

                M[0, 2] += (new_w / 2) - center[0]
                M[1, 2] += (new_h / 2) - center[1]

                # 对原始彩色图像应用旋转
                # borderValue=(255, 255, 255): 彩色图像的白色背景
                rotated = cv2.warpAffine(image, M, (new_w, new_h),
                                      flags=cv2.INTER_LANCZOS4,
                                      borderMode=cv2.BORDER_CONSTANT,
                                      borderValue=(255, 255, 255))
                return rotated

            return image

        except Exception:
            return image # 出错时返回原图

    @staticmethod
    def _enhance_contrast(image):
        """
        对灰度图像进行温和的对比度增强。
        原理: 使用CLAHE (Contrast Limited Adaptive Histogram Equalization) 技术。
              与全局直方图均衡不同，CLAHE在图像的局部区域进行直方图均衡，
              能更好处理光照不均的情况。通过 clipLimit 参数限制对比度放大的幅度，
              避免噪声被过度放大。之后再与原图混合，使效果更自然。
        """
        try:
            # 创建CLAHE对象，设置 clipLimit=1.5 (较低，表示温和增强)
            # tileGridSize=(4,4) 表示将图像划分为4x4的网格进行局部处理
            clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(4, 4))
            # 应用CLAHE到灰度图像
            enhanced = clahe.apply(image)

            # 将增强后的图像 (70%权重) 与原始图像 (30%权重) 进行加权混合
            # 这样做可以使增强效果更平滑，避免过于突兀
            result = cv2.addWeighted(image, 0.3, enhanced, 0.7, 0)

            return result
        except Exception:
            return image # 出错时返回原图

    @staticmethod
    def _enhance_contrast_color(image):
        """
        对彩色图像进行温和的对比度增强。
        原理: 将彩色图像从BGR色彩空间转换到LAB色彩空间。
              LAB空间中，L通道代表亮度，A和B通道代表颜色。
              仅对L (亮度) 通道应用CLAHE进行对比度增强，保持颜色信息不变。
              增强后再转换回BGR空间。同样与原始亮度通道混合。
        """
        try:
            # 将BGR图像转换为LAB色彩空间
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            # 分离L, A, B三个通道
            l, a, b = cv2.split(lab)

            # 对L (亮度) 通道应用温和的CLAHE
            clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(4, 4))
            cl = clahe.apply(l)

            # 将增强后的亮度通道与原始亮度通道混合
            cl = cv2.addWeighted(l, 0.3, cl, 0.7, 0)

            # 合并增强后的L通道以及原始的A, B颜色通道
            enhanced_lab = cv2.merge((cl, a, b))
            # 将LAB图像转换回BGR色彩空间
            enhanced_bgr = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

            return enhanced_bgr
        except Exception:
            return image # 出错时返回原图

    @staticmethod
    def _reduce_noise(image):
        """
        对灰度图像进行温和的降噪处理。
        原理: 使用 `cv2.fastNlMeansDenoising`，这是一种非局部均值降噪算法，
              它考虑图像中相似的区域来平滑像素，能较好地去除噪声同时保留边缘。
              参数h控制滤波强度。之后与原图混合以保留更多细节。
        """
        try:
            # 应用快速非局部均值降噪
            # h=5: 滤波强度参数，值越小，降噪程度越低，保留细节越多
            # searchWindowSize=15, templateWindowSize=5: 算法搜索和比较窗口的大小
            denoised = cv2.fastNlMeansDenoising(image, None, h=5, searchWindowSize=15, templateWindowSize=5)

            # 将降噪后的图像 (60%权重) 与原始图像 (40%权重) 进行加权混合
            # 目的是在降噪的同时，尽可能保留原始图像的细节
            result = cv2.addWeighted(image, 0.4, denoised, 0.6, 0)

            return result
        except Exception:
            return image # 出错时返回原图

    @staticmethod
    def _smart_sharpen(image):
        """
        对灰度图像进行智能锐化，避免过度锐化。
        原理: 使用非锐化掩模 (Unsharp Masking) 方法。
              基本思想是从原图中减去一个模糊版本的图像（高斯模糊），得到包含边缘信息的掩模，
              然后将这个掩模按一定权重加回到原图中，从而增强边缘，使图像看起来更清晰。
              最后使用np.clip限制像素值范围，防止溢出。
        """
        try:
            # 对图像进行高斯模糊，kernel_size=(3,3), sigma=1.0
            gaussian = cv2.GaussianBlur(image, (3, 3), 1.0)
            # 应用非锐化掩模: result = image * (1 + weight) - blurred_image * weight
            # 这里是 image * 1.5 + gaussian * (-0.5)
            unsharp_mask = cv2.addWeighted(image, 1.5, gaussian, -0.5, 0)

            # 将结果图像的像素值裁剪到 [0, 255] 范围内，并转换为uint8类型
            # 这是为了防止锐化操作导致像素值超出有效范围
            result = np.clip(unsharp_mask, 0, 255).astype(np.uint8)

            return result
        except Exception:
            return image # 出错时返回原图

    @staticmethod
    def _adaptive_binarize(image):
        """
        对灰度图像进行自适应二值化处理。
        原理: 二值化是将图像转换为只有黑白两种像素的过程。
              自适应阈值方法会根据像素邻域的特性来确定该像素的阈值，
              对于光照不均的图像效果通常优于全局阈值。
              此方法尝试Otsu和自适应高斯阈值，并选择效果更好（基于拉普拉斯方差评估边缘清晰度）的一个。
        """
        try:
            # 方法1: Otsu's Binarization
            # Otsu方法会自动找到一个全局最优阈值，将图像分为前景和背景
            _, otsu_binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # 方法2: Adaptive Gaussian Thresholding
            # cv2.ADAPTIVE_THRESH_GAUSSIAN_C: 阈值是根据邻域像素的高斯加权和计算的
            # cv2.THRESH_BINARY: 标准的二值化方法 (大于阈值为maxval，否则为0)
            # 15: 邻域大小 (block_size), 必须是奇数
            # 8: 从均值或加权均值中减去的常数C
            adaptive_binary = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                                  cv2.THRESH_BINARY, 15, 8)

            # 评估两种二值化结果的质量，通过计算拉普拉斯算子的方差
            # 拉普拉斯方差可以衡量图像的边缘数量和强度，方差越大通常表示边缘越清晰
            otsu_variance = cv2.Laplacian(otsu_binary, cv2.CV_64F).var()
            adaptive_variance = cv2.Laplacian(adaptive_binary, cv2.CV_64F).var()

            # 选择方差较大 (边缘更清晰) 的二值化结果
            if otsu_variance > adaptive_variance:
                return otsu_binary
            else:
                return adaptive_binary

        except Exception:
            # 如果自适应方法失败，回退到使用一个简单的全局阈值 (127) 进行二值化
            _, binary = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY)
            return binary