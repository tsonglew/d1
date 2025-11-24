import sys

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget


class BubbleWidget(QWidget):
    def __init__(self, text, parent=None):
        super().__init__(parent)

        # 1. 设置透明背景
        # 这很重要，否则圆角矩形外面的四个角会是黑的或灰的
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 2. 视觉参数配置
        self.border_width = 4  # 边框粗细
        self.border_radius = 15  # 圆角半径
        self.tail_height = 20  # 尾巴高度
        self.tail_width = 30  # 尾巴宽度
        self.tail_pos_offset = 40  # 尾巴距离左边的距离

        # 3. 设置内部文字控件
        self.label = QLabel(text)
        self.label.setWordWrap(True)  # 允许自动换行
        self.label.setStyleSheet("color: black; font-size: 16px; font-weight: bold;")

        # 4. 使用布局管理器来安放文字
        layout = QVBoxLayout(self)
        # 设置边距: (左, 上, 右, 下)
        # 下边距要大一点，因为要留位置给尾巴(tail_height)
        layout.setContentsMargins(20, 20, 20, 20 + self.tail_height)
        layout.addWidget(self.label)

    def paintEvent(self, event):
        """
        重写绘图事件，绘制气泡背景
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)  # 开启抗锯齿，让线条平滑

        # --- A. 准备画笔和画刷 ---
        pen = QPen(QColor("black"))
        pen.setWidth(self.border_width)
        painter.setPen(pen)

        painter.setBrush(QBrush(QColor("white")))

        # --- B. 计算绘制区域 ---
        # 需要考虑边框的一半宽度，防止线条被切掉
        rect_x = self.border_width / 2
        rect_y = self.border_width / 2
        rect_w = self.width() - self.border_width
        # 高度要减去尾巴的高度
        rect_h = self.height() - self.tail_height - self.border_width

        # --- C. 创建路径 (QPainterPath) ---

        # 1. 主体：圆角矩形
        path_rect = QPainterPath()
        rect_shape = QRectF(rect_x, rect_y, rect_w, rect_h)
        path_rect.addRoundedRect(rect_shape, self.border_radius, self.border_radius)

        # 2. 尾巴：三角形
        path_tail = QPainterPath()
        tail_start_x = rect_x + self.tail_pos_offset
        tail_start_y = rect_y + rect_h

        # 定义三角形的三个点
        p1 = QPointF(tail_start_x, tail_start_y)  # 基座左点
        p2 = QPointF(tail_start_x + self.tail_width, tail_start_y)  # 基座右点
        # 尾巴尖端 (指向左下)
        p3 = QPointF(tail_start_x - 10, tail_start_y + self.tail_height)

        # 绘制三角形路径
        path_tail.moveTo(p1)
        path_tail.lineTo(p3)
        path_tail.lineTo(p2)
        path_tail.closeSubpath()  # 闭合路径

        # --- D. 合并路径 (关键步骤) ---
        # .united 会将两个形状融合，自动消除重叠部分的边框线
        final_path = path_rect.united(path_tail)

        # --- E. 绘制最终路径 ---
        painter.drawPath(final_path)


# --- 测试主程序 ---
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 创建主窗口作为背景演示
    main_window = QWidget()
    main_window.setWindowTitle("PySide6 气泡对话框示例")
    main_window.resize(600, 400)
    main_window.setStyleSheet("background-color: #CCCCCC;")  # 灰色背景方便看效果

    # 创建气泡
    bubble = BubbleWidget(
        "你好！这是一个 PySide6 实现的自适应大小气泡。\n无论文字多长，边框都会自动调整。", main_window
    )
    bubble.move(50, 50)
    bubble.resize(300, 150)  # 设置初始大小，但布局会根据内容撑开

    # 再创建一个短的
    bubble2 = BubbleWidget("简短回复", main_window)
    bubble2.move(400, 200)
    bubble2.resize(150, 100)

    main_window.show()
    sys.exit(app.exec())
