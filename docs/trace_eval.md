# 📊 BÁO CÁO GIÁM SÁT & ĐÁNH GIÁ (OBSERVABILITY TRACE LOGS)
*Dành cho Role 5: Observability & Reviewer*

---

## 🎯 1. BẢNG CHẤM ĐIỂM AGENTIC FIT (SCORING MATRIX)

| Tiêu chí | Điểm (1-5) | Lý do đánh giá |
| :--- | :---: | :--- |
| 🧠 **Multi-step Reasoning** | `4/5` | Để xử lý một yêu cầu đổi trả, agent phải suy luận qua nhiều bước tuần tự: xác định đơn hàng → kiểm tra trạng thái giao hàng → đối chiếu chính sách đổi trả (thời hạn, tình trạng sản phẩm) → quyết định hướng xử lý (hoàn tiền/đổi hàng/từ chối). Đây không phải câu hỏi 1 bước mà là một chuỗi suy luận có phụ thuộc lẫn nhau.. |
| 🛠️ **Tool Interaction** | `5/5` | Cần gọi nhiều công cụ khác nhau: lookup_order() (tra cứu đơn hàng), check_return_policy() (kiểm tra chính sách theo danh mục sản phẩm), check_refund_eligibility(), create_return_request(), generate_shipping_label(). Không có tool thì hệ thống không thể lấy dữ liệu thực tế (đơn hàng của khách nằm trong DB, không có trong tri thức LLM).. |
| 🔀 **Dynamic Decision** | `4/5` | Luồng xử lý rẽ nhánh mạnh: sản phẩm lỗi vs. đổi ý; còn trong hạn vs. hết hạn; đã thanh toán online vs. COD; có ảnh chứng minh lỗi hay không. Agent phải chọn đúng nhánh dựa trên observation trả về từ tool, không thể lập trình cứng if-else vì input ngôn ngữ tự nhiên rất đa dạng. |
| ⏳ **Long Horizon** | `3/5` | Có yếu tố đa lượt (khách có thể cần gửi ảnh sản phẩm lỗi ở lượt sau, hoặc quay lại hỏi tiếp về trạng thái hoàn tiền), nhưng phần lớn use-case hoàn tất trong 1 phiên hội thoại ngắn (vài lượt), không kéo dài qua nhiều ngày như một dự án phức tạp — nên không đạt điểm tối đa. |
| **TỔNG ĐIỂM FIT** | **16/20** | **KẾT LUẬN: BÀI TOÁN RẤT NÊN DÙNG REACT AGENT! Sự kết hợp giữa dữ liệu động (đơn hàng, tồn kho, chính sách) và logic rẽ nhánh phức tạp khiến chatbot thuần LLM không thể xử lý chính xác.** |

---

## 🔍 2. SO SÁNH PHẢN HỒI (TEST CASE #3)

**Câu hỏi**: "Tôi mua đôi giày mã đơn #DH7789 hôm 10 ngày trước, giờ thấy bị lỗi keo dán đế, tôi muốn đổi trả."

### 🤖 Chatbot Baseline:
* **Phản hồi**: "Bạn có thể đổi trả trong vòng 30 ngày nếu sản phẩm lỗi do nhà sản xuất. Vui lòng liên hệ tổng đài để được hỗ trợ."
* **Nhận xét**: Trả lời chung chung, không xác nhận được đơn hàng #DH7789 có thực sự tồn tại, có đúng 10 ngày không, sản phẩm có thuộc diện được đổi trả (giày có thể có chính sách riêng khác quần áo) hay chưa — đẩy việc xử lý thực tế ngược lại cho con người.

### 🧠 ReAct Agent:
* **Thought 1**: Cần xác minh đơn hàng #DH7789 có tồn tại và lấy ngày mua thực tế.
* **Action 1**: `lookup_order['DH7789']`
* **Observation 1**: Đơn hàng: Giày Sneaker XYZ, ngày giao 10 ngày trước, trạng thái: đã giao thành công.
* **Thought 2**: Cần kiểm tra chính sách đổi trả riêng cho danh mục giày và lỗi "keo dán đế".
* **Action 2**: `check_return_policy['category=giày', 'reason=lỗi sản xuất']`
* **Observation 2**: Giày: đổi trả trong 15 ngày nếu lỗi nhà sản xuất, cần ảnh minh chứng
* **Thought 3:** Đơn hàng còn trong hạn (10/15 ngày), lỗi thuộc diện được chấp nhận, nhưng cần khách cung cấp ảnh trước khi tạo yêu cầu chính thức.
* **Final Answer**: "Đơn #DH7789 vẫn còn trong thời hạn đổi trả (15 ngày với lỗi sản xuất). Bạn vui lòng gửi 2-3 ảnh phần đế bị lỗi keo để mình tạo yêu cầu đổi trả ngay nhé!"
* **Nhận xét**: Xác minh dữ liệu thật, áp đúng chính sách theo danh mục, và chủ động dẫn dắt bước tiếp theo thay vì đẩy việc cho khách tự tìm hiểu.