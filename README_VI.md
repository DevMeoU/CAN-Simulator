[🇬🇧 English Version](README.md)

# CanSimulate - Mô phỏng mạng CAN Bus

Dự án này cung cấp các công cụ để mô phỏng và giao tiếp trên mạng CAN (Controller Area Network) sử dụng Python. Nó bao gồm các kịch bản để gửi, nhận tin nhắn và một giao diện đồ họa (GUI) toàn diện mô phỏng các ECU trên ô tô.

## Yêu cầu hệ thống

*   Python 3.x
*   Thư viện Python:
    *   `python-can`
    *   `cantools`
    *   `tkinter` (thường có sẵn khi cài python trên Windows)
*   Phần cứng/Driver CAN (mặc định hỗ trợ Kvaser, có thể cấu hình lại trong code).

Cài đặt các thư viện cần thiết:
```bash
pip install python-can cantools
```

## Cấu trúc dự án

Dự án bao gồm 3 file mã nguồn chính trong thư mục `cantools/src/cantools`:

1.  **`Can_Message_Receive.py`**: Kịch bản nhận và giải mã tin nhắn CAN.
2.  **`Can_Message_Send.py`**: Kịch bản gửi tin nhắn CAN giả lập.
3.  **`Simulation_GUI.py`**: Ứng dụng giao diện mô phỏng đa node (ECM, ABS, Cluster, Gateway).

---

## Chi tiết các module

### 1. Nhận tin nhắn (`Can_Message_Receive.py`)

File này thiết lập kết nối tới bus CAN và lắng nghe các tin nhắn gửi đến trong vòng lặp vô tận.

*   **Chức năng**:
    *   Kết nối tới interface `kvaser`, channel 0.
    *   Load file DBC (`Sample_DBC_Kvaser.dbc`) để giải mã tín hiệu.
    *   In ra màn hình số thứ tự, ID, dữ liệu raw (hex) và dữ liệu đã giải mã của tin nhắn nhận được.
*   **Sử dụng khi**: Bạn muốn kiểm tra xem bus có tin nhắn nào không và nội dung của chúng là gì.

**Cách chạy:**
```bash
python cantools/src/cantools/Can_Message_Receive.py
```

### 2. Gửi tin nhắn (`Can_Message_Send.py`)

File này giả lập việc phát một chuỗi tin nhắn cụ thể lên mạng CAN.

*   **Chức năng**:
    *   Kết nối tới interface `kvaser`, channel 1.
    *   Tạo tin nhắn `ABS_Wheel_Speed` (ID 0x12C) với dữ liệu mẫu.
    *   Gửi liên tục 100 tin nhắn với khoảng cách 0.1s mỗi tin.
*   **Lưu ý**: File này được cấu hình dùng **Channel 1**. Điều này hữu ích khi bạn muốn test giao tiếp giữa Channel 1 (Gửi) và Channel 0 (Nhận/GUI) trên cùng một thiết bị hoặc máy tính.

**Cách chạy:**
```bash
python cantools/src/cantools/Can_Message_Send.py
```

### 3. Giao diện mô phỏng (`Simulation_GUI.py`)

Đây là ứng dụng chính, mô phỏng một hệ thống mạng CAN trên ô tô hoàn chỉnh với các ECU ảo tương tác với nhau.

*   **Các Node mô phỏng**:
    *   **ECM (Engine Control Module)**: 
        *   Điều khiển RPM thông qua thanh trượt.
        *   Nhận thông tin Ignition (từ Cluster) và Tốc độ (từ ABS) để hiển thị.
    *   **ABS (Anti-lock Braking System)**: 
        *   Nhập và gửi tốc độ bánh trước/sau.
        *   Nhận RPM (từ ECM) và cảnh báo đỏ nếu RPM quá cao (>5000).
    *   **Cluster (Đồng hồ táp-lô)**: 
        *   Gửi trạng thái Ignition (Bật/Tắt).
        *   Hiển thị RPM và Tốc độ xe nhận được từ mạng CAN như một dashboard thật.
    *   **Gateway**: 
        *   Đóng vai trò giám sát, hiển thị log các tin nhắn được định tuyến qua mạng.

*   **Cách hoạt động**:
    *   Ứng dụng kết nối tới `kvaser` channel 0.
    *   Sử dụng chế độ `receive_own_messages=True` để các node ảo trong cùng một app có thể "nghe" thấy tin nhắn của nhau.
    *   Sử dụng Thread riêng để lắng nghe tin nhắn đến mà không làm đơ giao diện.

**Cách chạy:**
```bash
python cantools/src/cantools/Simulation_GUI.py
```

## Lưu ý cấu hình đường dẫn

Trong mã nguồn, đường dẫn tới file DBC đang được đặt cứng (hardcoded):
`D:/Workspace/Embedded/CanSimulate/Sample_DBC_Kvaser.dbc`

Nếu bạn di chuyển dự án hoặc chạy trên máy khác, vui lòng:
1.  Đảm bảo file `.dbc` tồn tại.
2.  Cập nhật biến `CAN_DBC_PATH` hoặc `dbc_path` trong 3 file Python trên để trỏ đúng tới vị trí file `.dbc` của bạn.
