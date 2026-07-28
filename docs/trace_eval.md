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

**Câu hỏi**: "Đơn hàng #DH1023 của tôi hiện đang ở đâu rồi?."

### 🤖 Chatbot Baseline:
* **Phản hồi**: "Dạ, em chào anh/chị ạ! Cảm ơn anh/chị đã liên hệ với bộ phận chăm sóc khách hàng của bên em.

Về đơn hàng mã **#DH1023** của anh/chị, em rất tiếc phải thông tin rằng, với vai trò là trợ lý ảo, hiện tại em không có quyền truy cập trực tiếp vào hệ thống cơ sở dữ liệu để kiểm tra thông tin thực tế cũng như định vị chính xác trạng thái đơn hàng của mình được ạ.

Để kiểm tra xem đơn hàng **#DH1023** hiện đang ở đâu, anh/chị có thể dễ dàng tự tra cứu qua các cách sau:

1. **Kiểm tra trên Ứng dụng/Website:** Anh/chị vui lòng đăng nhập tài khoản mua hàng, vào mục **"Đơn mua"** -> chọn đơn hàng **#DH1023**. Tại đây, hệ thống sẽ hiển thị chi tiết lộ trình vận chuyển và thời gian dự kiến giao hàng.
2. **Kiểm tra Email:** Hệ thống luôn gửi email cập nhật trạng thái khi đơn hàng bắt đầu được vận chuyển. Anh/chị thử kiểm tra hộp thư đến (hoặc hộp thư rác/quảng cáo) của mình nhé.
3. **Liên hệ Nhân viên hỗ trợ:** Nếu cần kiểm tra nhanh từ nhân viên có thẩm quyền truy cập hệ thống, anh/chị có thể nhấn vào nút **"Chat với nhân viên hỗ trợ"** ngay trên ứng dụng hoặc liên hệ hotline chăm sóc khách hàng để được các bạn tổng đài viên kiểm tra trực tiếp cho mình ạ.

Bên cạnh việc tra cứu đơn hàng, nếu anh/chị có thêm câu hỏi nào về **chính sách đổi trả** hay hoàn tiền của sàn, em rất sẵn lòng hỗ trợ giải đáp ngay cho anh/chị!

Chúc anh/chị một ngày thật nhiều niềm vui ạ!"
* **Nhận xét**: Trả lời theo thẩm quyền được thiết kế trong Prompt khi không có quyền hạn truy cập cơ sở dữ liệu. Hướng dẫn được người dùng cách tra cứu theo các lựa chọn như Website/Email/hoặc liên hệ nhân viên hỗ trợ - Đẩy thông tin cho người dùng.

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

3