import sys
import json
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt

class MessageFormatter(QWidget):
    def __init__(self):
        super().__init__()
        self.tag_names = {}
        self.container_tags = set(['6F', '70', 'A5', 'BF0C', 'BF20', 'E1'])
        self.as2805_fields = {}
        self.load_tag_params()
        self.load_as2805_fields()
        self.initUI()

    def load_tag_params(self):
        script_dir = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(script_dir, 'tagsdef.json')
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as file:
                    self.tag_names = json.load(file)
                print("Tag definitions loaded successfully.")
            except json.JSONDecodeError:
                print("Error: Invalid JSON in tagsdef.json")
            except IOError:
                print("Error: Unable to read tagsdef.json")
        else:
            print("tagsdef.json not found. Starting without tag name parsing.")

    def load_as2805_fields(self):
        script_dir = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(script_dir, 'as2805fields.json')
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as file:
                    self.as2805_fields = json.load(file)
                print("AS2805 field definitions loaded successfully.")
            except json.JSONDecodeError:
                print("Error: Invalid JSON in as2805fields.json")
            except IOError:
                print("Error: Unable to read as2805fields.json")
        else:
            print("as2805fields.json not found. Using default AS2805 field definitions.")
            self.as2805_fields = {
                "1": {"name": "Bitmap", "length": "8"},
                "2": {"name": "Primary Account Number (PAN)", "length": "Variable"},
                "3": {"name": "Processing Code", "length": "6"},
                "4": {"name": "Amount, Transaction", "length": "12"},
                "7": {"name": "Transmission Date and Time", "length": "10"},
                "11": {"name": "System Trace Audit Number", "length": "6"},
                "12": {"name": "Time, Local Transaction", "length": "6"},
                "13": {"name": "Date, Local Transaction", "length": "4"},
                "15": {"name": "Settlement Date", "length": "4"},
                "18": {"name": "Merchant Type", "length": "4"},
                "32": {"name": "Acquiring Institution Identification Code", "length": "Variable"},
                "37": {"name": "Retrieval Reference Number", "length": "12"},
                "41": {"name": "Card Acceptor Terminal Identification", "length": "8"},
                "42": {"name": "Card Acceptor Identification Code", "length": "15"},
                "43": {"name": "Card Acceptor Name/Location", "length": "40"},
                "48": {"name": "Additional Data - Private", "length": "Variable"},
                "49": {"name": "Currency Code, Transaction", "length": "3"}
            }

    def initUI(self):
        self.setWindowTitle('Message Formatter')
        self.setGeometry(100, 100, 800, 600)

        layout = QHBoxLayout()

        # Left side - Input
        left_layout = QVBoxLayout()
        left_label = QLabel("Input Data:")
        self.input_text = QTextEdit()
        left_layout.addWidget(left_label)
        left_layout.addWidget(self.input_text)

        # Right side - Output
        right_layout = QVBoxLayout()
        right_label = QLabel("Formatted Data:")
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        right_layout.addWidget(right_label)
        right_layout.addWidget(self.output_text)

        # Buttons
        button_layout = QVBoxLayout()
        tlv_button = QPushButton("Format TLV")
        tlv_button.clicked.connect(self.format_tlv)
        as2805_button = QPushButton("Parse AS2805")
        as2805_button.clicked.connect(self.parse_as2805)
        button_layout.addWidget(tlv_button)
        button_layout.addWidget(as2805_button)

        # Add layouts to main layout
        layout.addLayout(left_layout)
        layout.addLayout(button_layout)
        layout.addLayout(right_layout)

        self.setLayout(layout)

    def format_tlv(self):
        input_data = self.input_text.toPlainText().strip()
        formatted_data = self.parse_tlv(input_data)
        self.output_text.setHtml(formatted_data)

    def parse_tlv(self, data, indent=0):
        formatted = ""
        i = 0
        while i < len(data):
            if i + 2 > len(data):
                formatted += "&nbsp;" * (indent * 4)
                formatted += f"<span style='color:red;'>{data[i:]} Error: Incomplete TLV at position {i}</span><br>"
                break

            # Check if it's a multi-byte tag
            if data[i] in '5F':  # '5' and 'F' are common first bytes for 2-byte tags
                tag = data[i:i+4]
                i += 4
            else:
                tag = data[i:i+2]
                i += 2

            tag_name = self.tag_names.get(tag, "Unknown")
            formatted += "&nbsp;" * (indent * 4)
            formatted += f"<span style='color:blue;'>Type: {tag} ({tag_name})</span><br>"

            if i + 2 > len(data):
                formatted += "&nbsp;" * (indent * 4)
                formatted += f"<span style='color:red;'>{data[i:]} Error: Incomplete length for tag {tag} at position {i}</span><br>"
                break

            length = int(data[i:i+2], 16)
            formatted += "&nbsp;" * (indent * 4)
            formatted += f"<span style='color:green;'>Length: {length}</span><br>"
            i += 2

            if i + length*2 > len(data):
                formatted += "&nbsp;" * (indent * 4)
                formatted += f"<span style='color:purple;'>Value: {data[i:]}</span><br>"
                formatted += "&nbsp;" * (indent * 4)
                formatted += f"<span style='color:red;'>Error: Incomplete value for tag {tag} at position {i}</span><br>"
                break

            value = data[i:i+length*2]
            if tag in self.container_tags:
                formatted += "&nbsp;" * (indent * 4)
                formatted += f"<span style='color:purple;'>Value:</span><br>"
                formatted += self.parse_tlv(value, indent + 1)
            else:
                formatted += "&nbsp;" * (indent * 4)
                formatted += f"<span style='color:purple;'>Value: {value}</span><br>"
            
            formatted += "<br>"
            i += length*2

        return formatted

    def parse_as2805(self):
        input_data = self.input_text.toPlainText().strip()
        formatted_data = self.format_as2805(input_data)
        self.output_text.setHtml(formatted_data)

    def format_as2805(self, data):
        formatted = ""
        try:
            # Parse MTI (Message Type Indicator)
            mti = data[:4]
            formatted += f"<span style='color:blue;'>MTI: {mti}</span><br><br>"
            
            # Parse bitmap
            bitmap = data[4:20]  # Assuming 8-byte (64-bit) primary bitmap
            binary_bitmap = ''.join(format(int(bitmap[i:i+2], 16), '08b') for i in range(0, len(bitmap), 2))
            
            formatted += f"<span style='color:green;'>Bitmap: {bitmap}</span><br>"
            formatted += f"<span style='color:green;'>Binary Bitmap: {binary_bitmap}</span><br><br>"

            # Parse data elements
            data_index = 20
            for i, bit in enumerate(binary_bitmap, start=1):
                if bit == '1':
                    field_info = self.as2805_fields.get(str(i), {"name": f"Field {i}", "length": "Variable"})
                    field_name = field_info["name"]
                    field_length = field_info["length"]

                    formatted += f"<span style='color:blue;'>Field {i}: {field_name}</span><br>"

                    if i == 1:  # Special handling for Field 1 (Bitmap)
                        formatted += f"<span style='color:purple;'>Value: {bitmap}</span><br><br>"
                        continue

                    if field_length == "Variable":
                        if data_index + 2 > len(data):
                            raise ValueError(f"Incomplete data for variable length field {i}")
                        length = int(data[data_index:data_index+2])
                        data_index += 2
                    else:
                        length = int(field_length)

                    if data_index + length > len(data):
                        raise ValueError(f"Incomplete data for field {i}")

                    value = data[data_index:data_index+length]
                    formatted += f"<span style='color:green;'>Length: {length}</span><br>"
                    formatted += f"<span style='color:purple;'>Value: {value}</span><br><br>"
                    data_index += length

            return formatted
        except Exception as e:
            error_msg = f"Error parsing AS2805 message: {str(e)}<br>"
            error_msg += f"Error occurred at data index: {data_index}<br>"
            error_msg += f"Partial formatted output:<br>{formatted}<br>"
            error_msg += f"Remaining unprocessed data: {data[data_index:]}<br>"
            return error_msg
    
def main():
    app = QApplication(sys.argv)
    ex = MessageFormatter()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()