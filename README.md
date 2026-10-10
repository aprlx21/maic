# MAIC Offline

Web nội bộ tạo giáo án, slide và lời giảng từ PDF, với phản biện và một lần duyệt cuối của giáo viên. MVP dành cho nhóm tin cậy, chưa có đăng nhập. Tên người duyệt là thông tin tự khai báo.

## Chạy bằng Docker Compose

Yêu cầu Docker Engine đang chạy và cổng 8000 còn trống:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
docker compose up --build -d
```

Mở **http://127.0.0.1:8000**. Compose gồm FastAPI, worker LangGraph, PostgreSQL, MinIO; image có LibreOffice, OCR tiếng Việt/Anh và Noto Sans. Font giao diện được đóng gói cùng ứng dụng.

Mặc định `MAIC_MODE=demo`: chạy quy trình bằng nội dung mẫu dựa trên PDF, không gọi model. Phần kiểm tra AI trong demo trả kết quả giả lập; chỉ các kiểm tra cấu trúc, nguồn và DeckKit/lint là thật. Bản demo được gắn nhãn, không dùng để đánh giá chất lượng AI.

Để dùng model thật, sửa `.env` rồi chạy lại `docker compose up -d`:

```dotenv
MAIC_MODE=openai
OPENAI_API_KEY=your-key
MAIC_MODEL=gpt-6-luna
```

Model phải hỗ trợ Responses API, Structured Outputs và ảnh đầu vào; có thể thay bằng model được tài khoản cấp quyền. Điền ba biến đơn giá trong `.env.example` để tính chi phí từ usage API. Chưa điền đơn giá thì chi phí hiển thị chưa xác định. Đây là **quy trình chuẩn bị trước giờ học**; chế độ OpenAI vẫn cần kết nối API.

### Bảo vệ API key

- `.env` bị Git ignore. Trên máy Windows hiện tại, ACL của file đã được khóa cho tài khoản chạy ứng dụng, `Administrators` và `SYSTEM`; không còn quyền kế thừa cho nhóm Users.
- Web server không lưu API key vào model cấu hình, API `/config`, database hoặc giao diện. Với Compose, chỉ container worker nhận `OPENAI_API_KEY`. Khi chạy trực tiếp, worker nạp key ngay trước khi gọi SDK.
- Tiến trình con dùng để dựng slide và PDF bị loại `OPENAI_API_KEY`. Lỗi của worker được lọc các credential đã cấu hình trước khi ghi log hoặc lưu vào job.
- Key không được đưa vào lệnh shell, URL, database, log hoặc file artifact. Chỉ worker gửi key trong header xác thực của OpenAI SDK.
- Đổi key thì khởi động lại worker. Nếu nghi ngờ key đã từng bị lộ, thu hồi ở OpenAI và thay key mới trong `.env`.

Chỉ bind localhost theo mặc định. Để dùng trong LAN tin cậy, đặt `MAIC_BIND` thành địa chỉ LAN của máy chủ. Không đưa trực tiếp bản MVP chưa có xác thực lên Internet.

## Chạy trực tiếp trên Windows

Yêu cầu Python 3.11+, Node 22+, Git và LibreOffice hoặc Microsoft PowerPoint + Word đã kích hoạt. Adapter tự dùng Microsoft Office khi không có LibreOffice; đây là lựa chọn cho demo trên desktop, Docker/server vẫn dùng LibreOffice. Dùng Noto Sans hoặc đặt `MAIC_SLIDE_FONT=Arial`. PDF scan cần Tesseract language data `vie.traineddata`, `eng.traineddata`; đặt `MAIC_TESSDATA_PREFIX` đến thư mục chứa chúng. Có thể đặt `MAIC_SOFFICE` đến đường dẫn tuyệt đối của `soffice.exe`.

Trên máy demo đã cài phụ thuộc, chạy `powershell -File scripts/start-demo.ps1` rồi mở **http://127.0.0.1:8765**. Script khởi động web/worker ẩn, dùng Arial, giữ nguyên `.env`; key chỉ được worker nạp.

Cài mới tại thư mục dự án:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e '.[test]'
.\.venv\Scripts\python scripts/bootstrap_vendor.py
.\.venv\Scripts\python scripts/bootstrap_ocr.py
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
npm --prefix frontend ci
npm --prefix frontend run build
.\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Mở terminal thứ hai, cùng thư mục và `.env`:

```powershell
.\.venv\Scripts\python -m app.worker
```

Không cần PostgreSQL/MinIO khi chạy trực tiếp: mặc định SQLite + filesystem, checkpoint lưu riêng trong `data/checkpoints.db`. Khi phát triển frontend, `npm --prefix frontend run dev` proxy `/api` đến cổng 8000.

## Quy trình

1. **Gửi PDF:** môn/chủ đề, đối tượng, thời lượng, số slide và yêu cầu riêng. Kiểm tra định dạng, dung lượng, mật khẩu và số trang.
2. **Đọc nguồn:** PyMuPDF trích văn bản/bảng/hình và bbox từng trang; OCR chỉ trang thiếu text. PDF, ảnh và `ContentUnit` là nguồn chuẩn. Markdown theo trang là bản dẫn xuất có evidence ID, không được dùng để suy đoán số trang. Cây kiến thức hiện được nhóm theo heading, có confidence thấp khi phải dùng heuristic.
3. **Lead:** một lượt AI tạo giáo án, các phần kiến thức K, nội dung slide và gợi ý bố cục theo nội dung từ nguồn đã chọn. Python chọn bố cục dự phòng khi cần.
4. **Render:** DeckKit/lint dựng và kiểm tra slide theo các bố cục đã hỗ trợ. Không thực thi Python do model sinh.
5. **Script:** sau render, sinh lời giảng theo nhóm tối đa 8 slide mỗi lượt, kèm bảng ảnh của nhóm, hoạt động liên quan, nguồn và tiêu đề trước/sau. Chỉ sinh lại script bị mất hiệu lực, giữ lời giảng giáo viên sửa trực tiếp.
6. **Kiểm tra:** một lượt AI đánh giá cả sư phạm, nội dung, câu hỏi và bản render. Bốn tiêu chí vẫn có kết quả riêng nhưng không phải các Peer độc lập. Validator nguồn/cấu trúc và lint chạy bằng code. Mặc định **không tự sửa**; có thể bật tối đa hai vòng bằng `MAIC_MAX_AUTO_ROUNDS`.
7. **Giáo viên:** sửa trực tiếp hoặc yêu cầu AI sửa → revision mới → phản biện lại. Không duyệt revision cũ, khi đang xử lý, hoặc còn `blocked`. Finding `revise` cần sửa hoặc ghi lý do chấp nhận riêng.
8. **Xuất:** hash gắn nội dung, PDF nguồn và file đã phản biện. Kiểm tra lại checksum trước khi phát hành. Mỗi version có giáo án DOCX/PDF, PPTX với speaker notes, slide PDF, PDF handout có ảnh slide và toàn bộ lời giảng, cùng `package.json`. Package tách `ShowFile`, `ReadScript`, `AskQuestion` và đáp án. Bản đã phát hành giữ nguyên khi tạo revision/version tiếp theo.

`slides_maker` được pin tại commit `3767cc346d63ef1646082c87f15fbf0be582b152`, lưu trong [vendor/slides_maker.lock.json](vendor/slides_maker.lock.json). Đây là adapter cho quy trình MAIC; các cổng duyệt tương tác riêng của skill upstream được thay bằng lần duyệt cuối của giáo viên. Không tuyên bố đã chạy toàn bộ quy trình chứng nhận của upstream.

## LangGraph tối giản

Luồng mới và ngân sách được mô tả trong [LANGGRAPH_MINIMAL.md](LANGGRAPH_MINIMAL.md).
Lượt đầu cần `2 + ceil(số slide / 8)` lần gọi AI: với 8 slide là **3 lượt**, so với 15 lượt của luồng cũ.
Đây là số lượt theo cấu trúc luồng, không phải kết quả đo token/chi phí API thật.
Các giá trị mặc định: context 4.000 token; input ước tính mỗi lượt 32.000; output mỗi lượt tối đa 12.000;
mỗi job tối đa 90 lượt, 1.000.000 input và 40.000 output token. `.env` hiện có sẽ ghi đè mặc định;
xem `.env.example` để áp dụng cấu hình mới. Khởi động lại worker/web sau khi đổi mã hoặc cấu hình.

## Cache, chi phí và khôi phục

- Cache bản trích, OCR, Markdown và cây kiến thức theo SHA256 PDF + phiên bản parser. Cache render theo nội dung/bố cục; cache lời gọi model theo dữ liệu/prompt/schema/ảnh. Lời giảng chỉ đổi → tái sử dụng ảnh render, cập nhật notes.
- Token thực tế lấy từ Responses usage; token ngữ cảnh toàn nguồn/đã chọn chỉ là phép đo retrieval, không phải hai hóa đơn. Giá tiền tính theo đơn giá người vận hành khai báo.
- Lượt lỗi giữ mức token dự phòng bảo thủ khi chưa biết usage. Có giới hạn số lượt, input/output token theo job và theo lượt, cùng thời gian. Input admission dùng ước tính gồm prompt, schema và ảnh; không phải giới hạn token chính xác từ provider. Output bị chặn bằng `max_output_tokens`, bao gồm cả reasoning token. Không tự tăng ngân sách khi bấm thử lại.
- Checkpoint lưu sau mỗi node. Giáo viên duyệt bằng `interrupt`/`Command(resume=...)`. Nút thử lại tiếp tục checkpoint lỗi. Lease/heartbeat tránh hai worker nhận cùng job; SQLite phù hợp một worker, dùng PostgreSQL cho nhiều worker.
- OCR lỗi/không đọc được dừng ngay trước bước gọi AI. Cài dữ liệu OCR hoặc đưa lại PDF rõ hơn rồi thử lại. Cache bao gồm fingerprint dữ liệu OCR, mỗi job giữ snapshot nguồn riêng. OCR thành công vẫn cần đối chiếu công thức, bảng và ảnh gốc; model được nhận ảnh các trang OCR liên quan, tối đa 6 trang mỗi lượt.
- `bootstrap_ocr.py` tải dữ liệu tiếng Việt/Anh từ [Tesseract tessdata_fast 4.1.0](https://github.com/tesseract-ocr/tessdata_fast/tree/4.1.0), kiểm tra SHA256, lưu ở `data/tessdata`. Worker tự nhận thư mục này và không tự tải thêm dữ liệu.

## Kiểm thử và benchmark

```powershell
.\.venv\Scripts\python -m pytest -q --basetemp ./data/pytest
.\.venv\Scripts\python -m ruff check app tests scripts
npm --prefix frontend run build
npm --prefix frontend audit
docker compose config --quiet
```

Suite kiểm thử bao gồm trích nguồn/cache theo trang, OCR chọn trang, retrieval, checkpoint/retry, giới hạn hai vòng sửa, stale approval, finding chặn, lý do chấp nhận, checksum trước phát hành, speaker notes và version bất biến. Test workflow thay bộ chuyển PDF bằng fixture; test DeckKit gọi code upstream thật và kiểm tra lint phát hiện preview không khớp. Test render thật chạy khi có LibreOffice hoặc Microsoft Office; kiểm tra PDF slide, nội dung text và PDF giáo án.

Để đo **hai lượt chạy thực tế** gửi toàn nguồn và retrieval, bật chế độ OpenAI, khởi động web/worker, chuẩn bị PDF văn bản, scan và hỗn hợp:

```powershell
.\.venv\Scripts\python scripts/benchmark.py text.pdf scan.pdf mixed.pdf --subject 'Chu trình nước' --audience 'Lớp 6' --minutes 45 --slides 8 --output data/benchmark.json
```

Lệnh này tạo hai job cho mỗi PDF và phát sinh chi phí API theo cấu hình; không tự duyệt/phát hành. Báo cáo gồm token API, chi phí theo đơn giá, thời gian, tỷ lệ evidence ID hợp lệ và độ phủ content unit. **Evidence ID hợp lệ không chứng minh phát biểu đúng**: giáo viên cần chấm mức đầy đủ nội dung và độ đúng citation/ảnh/OCR trước khi quyết định hiệu quả retrieval. Chưa có kết quả chi phí API thật được đính kèm dự án.

## Các file chính

| Phần | File |
|---|---|
| API, upload, duyệt, tải file | `app/main.py` |
| Graph, revision và xuất bản | `app/workflow.py` |
| Queue, lease, khôi phục | `app/worker.py`, `app/db.py` |
| PDF, OCR, nguồn, retrieval | `app/document.py`, `app/context.py` |
| Lead, kiểm tra chung, script, Responses | `app/generation.py`, `app/llm.py` |
| slides_maker và xuất tài liệu | `app/rendering.py` |
| Giao diện giáo viên | `frontend/src/main.tsx` |

## Phạm vi đã kiểm chứng trên máy phát triển

Frontend build, API/workflow với fixture, DeckKit và lint đã được chạy. Microsoft PowerPoint đã render PPTX thành PDF thật; Word đã xuất giáo án PDF. Test render thật qua Office và test OCR scan đã đạt. PDF Vật lý 3 trang scan đã trích thành 35 content unit. Kết nối OpenAI với model `gpt-6-luna` đã thành công. Docker/LibreOffice runtime chưa được nghiệm thu trên máy này.
