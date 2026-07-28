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

## 3. TEST AGENT
**Question 1**  
```   
Tôi (Customer Phone 0901234567) mua áo khoác đơn OrderID #DH001 cách đây 5 ngày, size không vừa, tôi muốn đổi size lớn hơn.
```   
**Trace log**

```
------ Step 1 ------
Thought: Tôi cần tra cứu thông tin đơn hàng DH001 với số điện thoại 0901234567 để xác nhận sản phẩm và ngày giao hàng của khách hàng.
Action: lookup_order
Action Input: {"order_id": "DH001", "customer_phone": "0901234567"}

Observation
{
  "success": true,
  "message": "Tra cứu đơn hàng thành công.",
  "data": {
    "order": {
      "order_id": "DH001",
      "customer_name": "Nguyễn Văn An",
      "status": "delivered",
      "created_at": "2026-07-23",
      "delivered_at": "2026-07-25",
      "items": [
        {
          "item_id": "SP001",
          "product_name": "Tai nghe Bluetooth",
          "category": "dien_tu",
          "quantity": 1,
          "unit_price": 550000
        },
        {
          "item_id": "SP002",
          "product_name": "Áo sơ mi nam",
          "category": "thoi_trang",
          "quantity": 2,
          "unit_price": 350000
        }
      ]
    }
  }
}

------ Step 2 ------
Thought: Khách hàng báo mua "áo khoác" trong đơn hàng DH001, nhưng kết quả tra cứu đơn hàng DH001 chỉ có "Tai nghe Bluetooth" (SP001) và "Áo sơ mi nam" (SP002). Tôi cần kiểm tra chính sách đổi trả của danh mục "thoi_trang" (thời trang) để nắm rõ quy định trước khi tư vấn hoặc xử lý tiếp cho khách hàng về sản phẩm thời trang này.
Action: check_return_policy
Action Input: {"category": "thoi_trang"}

Observation
{
  "success": true,
  "message": "Tra cứu chính sách thành công.",
  "data": {
    "category": "thoi_trang",
    "policy": {
      "return_window_days": 14,
      "allow_refund": true,
      "require_original_packaging": false,
      "description": "Sản phẩm thời trang được đổi trả trong 14 ngày. Sản phẩm chưa qua giặt và còn nguyên tem."
    }
  }
}

------ Step 3 ------
Thought: Tôi đã có đủ thông tin để trả lời.

Final Answer: Chào anh/chị, qua kiểm tra hệ thống với số điện thoại **0901234567** và mã đơn hàng **#DH001** (giao ngày 25/07/2026), em nhận thấy đơn hàng của mình gồm có 2 sản phẩm:
1. **Tai nghe Bluetooth** (SP001)
2. **Áo sơ mi nam** (SP002)

Trong đơn hàng này không có sản phẩm **"áo khoác"** như anh/chị đề cập. Anh/chị vui lòng kiểm tra lại giúp em:
- Liệu sản phẩm anh/chị muốn đổi size có phải là **Áo sơ mi nam (SP002)** không ạ?
- Hoặc anh/chị có nhầm lẫn mã đơn hàng khác không?

**Thông tin thêm đến anh/chị:** Theo chính sách của cửa hàng, các sản phẩm thuộc danh mục Thời trang được hỗ trợ đổi trả trong vòng **14 ngày** kể từ ngày giao hàng thành công (đơn hàng của mình mới giao được 5 ngày nên vẫn hoàn toàn trong hạn hỗ trợ), với điều kiện sản phẩm chưa qua giặt và còn nguyên tem mác.

Ngay khi anh/chị xác nhận lại đúng thông tin sản phẩm/mã đơn hàng, em sẽ hỗ trợ tạo yêu cầu đổi size cho mình ngay nhé!   
```

===
**Question 2**  
```
Tôi mua Nồi chiên không dầu #DH002 từ 2 tháng trước, giờ mới phát hiện lỗi chỉ may, muốn đổi trả.
```

**Trace log**
```
------ Step 1 ------
Thought: Khách hàng chưa cung cấp số điện thoại và mã đơn hàng cụ thể (mã #DH002 có thể là mã đơn hàng hoặc mã sản phẩm, nhưng vẫn thiếu số điện thoại để tra cứu). Theo quy tắc an toàn, tôi cần yêu cầu khách hàng cung cấp đầy đủ thông tin này trước khi thực hiện tra cứu.

Final Answer: Chào bạn, để có thể tra cứu thông tin đơn hàng và hỗ trợ bạn tốt nhất về việc đổi trả sản phẩm "Nồi chiên không dầu", bạn vui lòng cung cấp thêm các thông tin sau giúp mình nhé:

1. **Số điện thoại** bạn đã dùng để đặt hàng.
2. Xác nhận giúp mình **#DH002** là mã đơn hàng của bạn hay là mã sản phẩm?

Ngay khi nhận được thông tin từ bạn, mình sẽ kiểm tra chính sách và hỗ trợ bạn các bước tiếp theo!

===== FINAL ANSWER =====
Chào bạn, để có thể tra cứu thông tin đơn hàng và hỗ trợ bạn tốt nhất về việc đổi trả sản phẩm "Nồi chiên không dầu", bạn vui lòng cung cấp thêm các thông tin sau giúp mình nhé:

1. **Số điện thoại** bạn đã dùng để đặt hàng.
2. Xác nhận giúp mình **#DH002** là mã đơn hàng của bạn hay là mã sản phẩm?

Ngay khi nhận được thông tin từ bạn, mình sẽ kiểm tra chính sách và hỗ trợ bạn các bước tiếp theo!
```
===
**Question 3**  
```
Tôi mua Nồi chiên không dầu có đơn #DH002 từ 2 tháng trước, giờ mới phát hiện lỗi không nấu cơm được, muốn đổi trả. Số điện thoại của tôi là 0912345678
```

**Trace log**
```
------ Step 1 ------
Thought: Tôi cần tra cứu thông tin đơn hàng DH002 với số điện thoại 0912345678 để kiểm tra thông tin sản phẩm và ngày giao hàng thực tế.
Action: lookup_order
Action Input: {"order_id": "DH002", "customer_phone": "0912345678"}

Observation
{
  "success": true,
  "message": "Tra cứu đơn hàng thành công.",
  "data": {
    "order": {
      "order_id": "DH002",
      "customer_name": "Trần Thị Bình",
      "status": "shipping",
      "created_at": "2026-07-26",
      "delivered_at": null,
      "items": [
        {
          "item_id": "SP003",
          "product_name": "Nồi chiên không dầu",
          "category": "gia_dung",
          "quantity": 1,
          "unit_price": 1800000
        }
      ]
    }
  }
}

------ Step 2 ------
Thought: Đơn hàng DH002 của khách hàng hiện đang có trạng thái "shipping" (đang giao hàng) và chưa có ngày giao hàng thực tế (delivered_at: null). Khách hàng báo đã mua từ 2 tháng trước và muốn đổi trả sản phẩm "Nồi chiên không dầu" (mã sản phẩm SP003, danh mục gia_dung) do "lỗi không nấu cơm được". Tôi cần kiểm tra chính sách đổi trả dành cho danh mục "gia_dung" để có thêm thông tin, đồng thời kiểm tra điều kiện đổi trả của đơn hàng này.
Action: check_return_policy
Action Input: {"category": "gia_dung"}

Observation
{
  "success": true,
  "message": "Tra cứu chính sách thành công.",
  "data": {
    "category": "gia_dung",
    "policy": {
      "return_window_days": 7,
      "allow_refund": true,
      "require_original_packaging": true,
      "description": "Sản phẩm gia dụng được đổi trả trong 7 ngày. Phải còn đầy đủ phụ kiện đi kèm."
    }
  }
}

------ Step 3 ------
Thought: Tôi cần kiểm tra xem đơn hàng DH002 với sản phẩm "Nồi chiên không dầu" (SP003) có đủ điều kiện đổi trả hay không bằng cách sử dụng công cụ check_refund_eligibility. Lý do khách hàng đưa ra là "lỗi không nấu cơm được" và tình trạng sản phẩm tạm thời xác định là đã qua sử dụng do khách mua từ trước.
Action: check_refund_eligibility
Action Input: {"order_id": "DH002", "customer_phone": "0912345678", "item_id": "SP003", "reason": "lỗi không nấu cơm được", "item_condition": "used"}

Observation
{
  "success": false,
  "message": "Đơn hàng chưa được giao.",
  "data": {
    "eligible": false,
    "order_id": "DH002",
    "item_id": "SP003"
  }
}

------ Step 4 ------
Thought: Tôi đã có đủ thông tin để trả lời.
Final Answer: Chào chị Trần Thị Bình, qua kiểm tra trên hệ thống với số điện thoại 0912345678, đơn hàng #DH002 chứa sản phẩm "Nồi chiên không dầu" (SP003) hiện tại vẫn đang trong trạng thái "Đang giao hàng" (shipping) và chưa được ghi nhận giao hàng thành công.

Vì đơn hàng chưa hoàn tất giao, hệ thống chưa thể tiếp nhận và xử lý yêu cầu đổi trả cho sản phẩm này. Ngoài ra, theo chính sách của ngành hàng gia dụng, thời hạn hỗ trợ đổi trả tối đa là trong vòng 7 ngày kể từ khi giao hàng thành công. Chị vui lòng kiểm tra lại thông tin đơn hàng hoặc liên hệ bộ phận vận chuyển để xác nhận lại tình trạng thực tế của đơn hàng nhé.
```