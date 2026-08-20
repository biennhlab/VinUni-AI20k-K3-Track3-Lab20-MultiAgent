# Lab Reflection Report

## §1. Giới thiệu
Trong Lab này, chúng ta đã tiến hành triển khai một hệ thống AI Multi-Agent (Đa tác vụ) hoàn chỉnh từ backend đến frontend. Hệ thống sử dụng LangGraph để điều phối các tác vụ phức tạp (Supervisor, Researcher, Analyst, Writer) và FastAPI để xây dựng API Backend hỗ trợ SSE (Server-Sent Events) streaming. Đích đến cuối cùng là tích hợp Local LLMs để phục vụ quá trình suy luận ngay trên máy cá nhân mà không phụ thuộc vào cloud API.

## §2. Chuẩn bị Môi trường & Models
Hệ thống được phát triển và chạy thử nghiệm trên máy cá nhân với cấu hình:
- **CPU**: AMD Ryzen 5 PRO 5650U
- **RAM**: 15GB 
- **GPU**: AMD Radeon(TM) Graphics
- **Hệ điều hành**: Windows 11 Pro

Về mặt Model, do giới hạn phần cứng (VRAM dùng chung), nhóm quyết định sử dụng mô hình tối ưu cho local là **Llama-3-8B-Instruct** phiên bản lượng tử hóa (Quantization) **Q4_K_M**. Model được tải về dưới định dạng `.gguf` để dễ dàng tương thích với `llama.cpp` hoặc `Ollama`. Các cài đặt môi trường như Python ảo (venv), các thư viện LangGraph, FastAPI cũng được chuẩn bị đầy đủ qua `pip`.

## §3. Cấu hình & Tối ưu hóa (Llama.cpp / vLLM / Ollama)
Vì chạy trên hệ thống có AMD tích hợp, chúng tôi chọn `llama.cpp` qua backend Ollama để tận dụng tối đa khả năng offload layer sang GPU.
Các thiết lập tối ưu:
- **Context Window**: 8192 tokens (để đảm bảo đủ không gian cho lịch sử đa tác vụ và các tool calls của LangGraph).
- **GPU Offload**: Offload tối đa các lớp mô hình sang GPU để giảm thiểu độ trễ sinh từ (latency/token).
- **Thread Count**: Được cấu hình dựa trên số core thực của Ryzen 5 để tối ưu hóa CPU inference khi GPU vRAM đầy.

## §4. Quá trình Benchmark
Quá trình benchmark được thực hiện nhằm so sánh sự khác biệt giữa Single-Agent (Direct LLM call) và Multi-Agent Pipeline.
- Kịch bản test: Yêu cầu phân tích kiến trúc "GraphRAG".
- Metrics ghi nhận:
  - Time to First Token (TTFT).
  - Inter-token Latency.
  - Tổng thời gian hoàn thành một Workflow toàn diện.

## §5. Phân tích Kết quả (Throughput, Latency, Resource Usage)
Kết quả thu được:
- **Tài nguyên**: GPU hoạt động ở mức ~85-95% khi sinh text, RAM hệ thống ổn định ở mức tiêu thụ 4-5GB cho model.
- **Latency**: TTFT trung bình tốn khoảng 1-2 giây. Tốc độ sinh từ (Throughput) đạt khoảng 15-20 tokens/s - khá ổn đối với card tích hợp.
- **Multi-Agent Overhead**: Do Multi-Agent đòi hỏi việc call LLM nhiều lần (cho từng Agent như Analyst, Writer), tổng thời gian xử lý (End-to-End Latency) tăng gấp 3-4 lần so với Single Agent. Bù lại, chất lượng đầu ra, tính logic và thông tin xác thực cao hơn hẳn nhờ sự phân chia luồng tư duy.

## §6. Multi-Agent & RAG Pipeline Integration (Nếu có)
Thay vì chỉ là CLI thông thường, toàn bộ Multi-Agent đã được bọc lại vào FastAPI endpoint `/api/chat`. Sự kết hợp giữa `astream` của LangGraph và SSE Streaming của FastAPI đã giúp Frontend có thể "vẽ" lại biểu đồ Timeline chi tiết của từng Agent ngay lập tức thay vì bắt người dùng chờ toàn bộ quá trình kéo dài 30 giây.

## §7. Khó khăn & Giải pháp
- **Khó khăn 1 (UX/UI Blocking)**: Ban đầu, việc chạy LangGraph Synchronous khiến FastAPI bị chặn, gây nghẽn kết nối và không stream được trạng thái tới UI.
  - **Giải pháp**: Chuyển sang sử dụng `graph_app.astream(state)` kết hợp Event Generator trong FastAPI để xử lý bất đồng bộ, giúp luồng giao diện mượt mà.
- **Khó khăn 2 (Ngốn RAM)**: Context Window của các Agents phình to ra sau mỗi bước truyền dữ liệu (State passing).
  - **Giải pháp**: Đặt giới hạn nội dung (`max_sources`) và tinh chỉnh prompt cô đọng lại cho Researcher Agent trước khi chuyển sang Analyst.

## §8. Tổng kết & Bài học rút ra
Việc xây dựng một hệ thống Multi-Agent AI trên Local Hardware là hoàn toàn khả thi và thực tế khi áp dụng các kỹ thuật Quantization và Streaming API hiện đại. Bài học đắt giá nhất là: Kiến trúc Multi-Agent mạnh hơn rất nhiều về suy luận, nhưng đi kèm cái giá về thời gian và tài nguyên. Vì thế, việc thiết kế một giao diện UI/UX tốt (có timeline, loading) là BẮT BUỘC để xoa dịu thời gian chờ đợi (latency tolerance) của người dùng cuối.
