# RunGuard

**Loại dự án:** Nền tảng khắc phục sự cố (remediation) DevOps/SRE hỗ trợ bởi AI.

**Phụ đề sản phẩm:** Trình biên dịch Runbook + Công cụ lập kế hoạch tự động khắc phục an toàn.

**Mục tiêu chính:** Xây dựng một công cụ ưu tiên Kubernetes, tích hợp AWS với chi phí thấp nhằm chuyển đổi runbook của con người thành chính sách máy có thể đọc được, điều tra sự cố, đề xuất kế hoạch và thực thi với các rào chắn (guardrails) an toàn.

**Đối tượng mục tiêu:** Kỹ sư DevOps, SRE, Kỹ sư nền tảng (Platform Engineers).

**Giá trị bổ trợ:** Hỗ trợ chuẩn bị cho các chứng chỉ AWS SAA, CKA, CKAD và DevOps Engineer Professional.

---

## 1. Tóm tắt điều hành
RunGuard không chỉ là một chatbot hay khung tự động hóa đơn thuần. Nó kết hợp bốn lớp cốt lõi:
1. **Trình biên dịch Runbook**: Chuyển đổi Markdown runbook thành chính sách cấu trúc và ràng buộc hành động.
2. **Công cụ suy luận sự cố**: Sử dụng dữ liệu alerts, logs, metrics, traces và sự kiện Kubernetes để tìm nguyên nhân gốc rễ.
3. **Công cụ chính sách an toàn**: Xác thực kế hoạch dựa trên phạm vi (scope), bán kính ảnh hưởng (blast radius) và quyền IAM.
4. **Bộ thực thi khắc phục**: Thực hiện các hành động đã phê duyệt (ưu tiên chế độ dry-run hoặc duyệt thủ công).

---

## 2. Vấn đề giải quyết
Các nhóm vận hành hiện nay thường đối mặt với:
* **Kiến thức phân mảnh**: Runbook nằm rải rác ở nhiều nơi hoặc chỉ là kiến thức truyền miệng.
* **Quá tải thông tin**: Cảnh báo đến từ nhiều nguồn (K8s, CloudWatch, Prometheus) gây khó khăn khi đối chiếu.
* **Rủi ro vận hành**: Khắc phục sai có thể làm tăng thời gian downtime hoặc gây lỗi dây chuyền.

---

## 3. Tầm nhìn sản phẩm
Trở thành một trợ lý sự cố thông minh cho các nhóm Platform:
* Đọc cảnh báo -> Tìm runbook phù hợp -> Chuyển đổi thành chính sách thực thi.
* Thu thập bằng chứng thực tế từ hạ tầng -> Đề xuất kế hoạch an toàn.
* Luôn ghi lại nhật ký: "Chuyện gì đã xảy ra, tại sao thực hiện, và làm sao để rollback".

---

## 4. Phạm vi dự án (MVP)

### Trong phạm vi (In Scope)
* Phân tích Runbook định dạng Markdown.
* Xử lý sự cố cho các workload trên Kubernetes.
* Tích hợp AWS (cảnh báo, tự động hóa, logging).
* Xác thực kế hoạch khắc phục qua chính sách và phê duyệt từ con người.
* Lưu trữ nhật ký kiểm tra (Audit logs).

### Ngoài phạm vi (Out of Scope)
* Hệ thống thanh toán SaaS đa người dùng.
* Quản lý tổ chức (Org admin) phức tạp.
* Tự động hóa hoàn toàn mà không cần con người phê duyệt.

---

## 5. Các chức năng cốt lõi

### 5.1 Trình biên dịch Runbook
* Đọc Markdown, trích xuất metadata (phạm vi, công cụ được phép/bị cấm, các bước rollback).
* Chuyển đổi thành dữ liệu JSON cấu trúc để máy thực thi.

### 5.2 Suy luận sự cố
* Tóm tắt sự cố, xác định nguyên nhân gốc rễ và thu thập bằng chứng hỗ trợ.
* Tạo danh sách kế hoạch khắc phục được xếp hạng.

### 5.3 Chính sách an toàn & Thực thi
* Kiểm tra bán kính ảnh hưởng và quyền IAM.
* Hỗ trợ các hành động rủi ro thấp: Restart Deployment, Scaling, thay đổi cấu hình Probes, hoặc chạy AWS SSM documents.

---

## 6. Kiến trúc kỹ thuật đề xuất

### Thành phần logic
* **Lớp tiếp nhận (Intake)**: EventBridge, API Gateway, Alertmanager.
* **Lớp xử lý**: AWS Step Functions điều phối Lambda (Planner & Policy Engine).
* **Lớp thực thi**: Kubernetes API Client, AWS SSM.
* **Lớp lưu trữ**: DynamoDB (Audit) & CloudWatch Logs.

### Công nghệ sử dụng
* **Backend**: Go hoặc Python.
* **Frontend**: Next.js hoặc Streamlit.
* **Infrastructure**: Terraform, Kubernetes (kind/k3d hoặc EKS), AWS Serverless.

---

## 7. Rào chắn an toàn (Mandatory Guardrails)
1. Không hành động nếu không khớp phạm vi (Scope match).
2. Không hành động nếu thiếu phương án hoàn tác (Rollback path).
3. Không hành động nếu bán kính ảnh hưởng vượt ngưỡng.
4. Yêu cầu phê duyệt thủ công cho các môi trường Production.

---

## 8. Kịch bản Demo tiêu biểu
1. **Pod CrashLoop**: Do cấu hình biến môi trường sai.
2. **Lỗi ImagePull**: Do tag ảnh không tồn tại hoặc sai quyền.
3. **Readiness Probe Failure**: Cấu hình sai probe gây lỗi traffic.
4. **AWS Automation**: Cảnh báo CloudWatch kích hoạt script khắc phục qua SSM trên sandbox.

---

## 9. Tại sao dự án này có giá trị trong Portfolio?
* Giải quyết vấn đề thực tế của SRE/DevOps.
* Chứng minh kỹ năng sâu về Kubernetes (CKA/CKAD) và AWS (DevOps Pro).
* Thể hiện tư duy về an toàn hệ thống, khả năng quan sát (observability) và kiến trúc hướng sự kiện.