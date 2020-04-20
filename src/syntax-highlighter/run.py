import re
import sys

import PyQt5
import PyQt5.QtWidgets


class SyntaxHighlighter(PyQt5.QtGui.QSyntaxHighlighter):
    def __init__(self, parent: PyQt5.QtGui.QTextDocument) -> None:
        super().__init__(parent)

        keyword_format = PyQt5.QtGui.QTextCharFormat()
        keyword_color = PyQt5.QtGui.QColor("red")
        keyword_format.setForeground(keyword_color)
        keywords = ["continue", "def", "if", "in", "is", "for", "not"]
        keyword_expressions: dict = {
            re.compile(fr"(?<!\w){keyword}(?!\w)"): keyword_format
            for keyword in keywords
        }

        singleton_format = PyQt5.QtGui.QTextCharFormat()
        singleton_color = PyQt5.QtGui.QColor("yellow")
        singleton_format.setForeground(singleton_color)
        singletons = ["None", "False"]
        singleton_expressions: dict = {
            re.compile(fr"(?<!\w){singleton}(?!\w)"): singleton_format
            for singleton in singletons
        }

        function_builtin_format = PyQt5.QtGui.QTextCharFormat()
        function_builtin_color = PyQt5.QtGui.QColor("green")
        function_builtin_format.setForeground(function_builtin_color)
        function_builtins = ["print"]
        function_builtin_expressions: dict = {
            re.compile(fr"{func}"): function_builtin_format
            for func in function_builtins
        }

        misc_characters_format = PyQt5.QtGui.QTextCharFormat()
        misc_characters_color = PyQt5.QtGui.QColor("purple")
        misc_characters_format.setForeground(misc_characters_color)
        misc_characters = ["(", ")", "[", "]", ":"]
        misc_characters_expressions: dict = {
            re.compile(re.escape(misc_character)): misc_characters_format
            for misc_character in misc_characters
        }

        string_format = PyQt5.QtGui.QTextCharFormat()
        string_color = PyQt5.QtGui.QColor("magenta")
        string_format.setForeground(string_color)
        string = re.compile(r"[\'\"].*?[\'\"]")
        string_expression: dict = {string: string_format}

        function_format = PyQt5.QtGui.QTextCharFormat()
        function_color = PyQt5.QtGui.QColor("green")
        function_format.setForeground(function_color)
        function = re.compile(r"(?<=def )\w*?(?=\(\):)")
        function_expression: dict = {function: function_format}

        comments_format = PyQt5.QtGui.QTextCharFormat()
        comments_color = PyQt5.QtGui.QColor("lightgray")
        comments_color.setAlpha(32)
        comments_format.setForeground(comments_color)
        comments = re.compile(r"#.*?$")
        comments_expression: dict = {comments: comments_format}

        whitespace_format = PyQt5.QtGui.QTextCharFormat()
        whitespace_color = PyQt5.QtGui.QColor("white")
        whitespace_color.setAlpha(32)
        whitespace_format.setForeground(whitespace_color)
        whitepspace = re.compile(r"(\t|[ ]{2,})")
        whitespace_expression: dict = {whitepspace: whitespace_format}

        # Create color, format and regex for `transparent` characters.
        transparent_color = PyQt5.QtGui.QColor(0, 0, 0, 0)
        transparent_format = PyQt5.QtGui.QTextCharFormat()
        transparent_format.setForeground(transparent_color)
        transparent = re.compile(r"(?<! ) (?! )")
        transparent_expression: dict = {transparent: transparent_format}

        """ Single `space` characters are *not* highlighted. Therefore it's
        important that `highlightBlock` formats the text in a strict order.
        First, all `mustache` syntax are set to the `mustache` format. Then all
        `tabs` and greater than two consecutive `whitespace` characters are set
        to the `whitespace` format. Finally, all `space` characters are set to
        the `transparent` format. """
        self._expressions = {
            **keyword_expressions,
            **singleton_expressions,
            **function_builtin_expressions,
            **function_expression,
            **string_expression,
            **misc_characters_expressions,
            **whitespace_expression,
            **comments_expression,
            **transparent_expression,
        }

    def highlightBlock(self, text: str):
        # See `SyntaxHighlighter.__init__()`.
        for expression, format_ in self._expressions.items():
            for match in expression.finditer(text):

                match_start = match.start()
                match_end = match.end()
                match_count = match_end - match_start

                self.setFormat(match_start, match_count, format_)


class MainWindow(PyQt5.QtWidgets.QFrame):
    def __init__(self) -> None:
        super(MainWindow, self).__init__(parent=None)

        self._init_ui()

    def _init_ui(self) -> None:

        self.setFixedSize(512, 512)

        self._plain_text_edit = PyQt5.QtWidgets.QPlainTextEdit(
            """
def my_function():
    # Do something!
    for item in ["hi!", None, False]:
        if not item:
            continue
        print(item)
        """.strip()
        )

        text_option = self._plain_text_edit.document().defaultTextOption()
        text_option.setFlags(
            text_option.flags() | PyQt5.QtGui.QTextOption.ShowTabsAndSpaces
        )
        self._plain_text_edit.document().setDefaultTextOption(text_option)

        self._syntax_highlighter = SyntaxHighlighter(
            parent=self._plain_text_edit.document()
        )

        layout = PyQt5.QtWidgets.QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(0)
        layout.addWidget(self._plain_text_edit)

        self.setStyleSheet(
            """
            QPlainTextEdit {

                font-family: Monaco, monospace;
                font-size: 14pt;
            }
        """
        )

        self.setLayout(layout)


if __name__ == "__main__":

    app = PyQt5.QtWidgets.QApplication([])

    main = MainWindow()
    main.show()

    sys.exit(app.exec_())
