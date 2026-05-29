# Tài liệu thiết kế — Course Document RAG Chatbot

Sơ đồ vẽ bằng **Mermaid** (xem trực tiếp trên GitHub hoặc VS Code Mermaid Preview).

Môn học demo: *Software Modeling and Design: UML, Use Cases, Patterns, and Software Architectures*.

---

## 1. Use Case Diagram (3 Actor: Admin, Lecturer, User)

```mermaid
graph LR
    Admin([👑 Admin])
    Lecturer([🎓 Lecturer])
    User([👤 User / Student])

    subgraph "Hệ thống RAG Chatbot"
        UC1[Đăng nhập / Đăng ký]
        UC2[Quản lý người dùng & phân quyền]
        UC3[Quản lý môn học / chương]
        UC4[Upload tài liệu PDF/DOCX/Slide]
        UC5[Xem danh sách tài liệu đã index]
        UC6[Xóa tài liệu]
        UC7[Chat hỏi đáp theo ngữ cảnh]
        UC8[Xem trích dẫn nguồn]
        UC9[Quản lý phiên chat của mình]
        UC10[Xem thống kê / lịch sử toàn hệ thống]
        UC11[Cấu hình hệ thống]
    end

    User --> UC1
    User --> UC5
    User --> UC7
    User --> UC8
    User --> UC9

    Lecturer --> UC1
    Lecturer --> UC3
    Lecturer --> UC4
    Lecturer --> UC5
    Lecturer --> UC6
    Lecturer --> UC7
    Lecturer --> UC8
    Lecturer --> UC9

    Admin --> UC1
    Admin --> UC2
    Admin --> UC3
    Admin --> UC4
    Admin --> UC5
    Admin --> UC6
    Admin --> UC7
    Admin --> UC9
    Admin --> UC10
    Admin --> UC11
```

**Quan hệ `<<include>>` / `<<extend>>`:**

```mermaid
graph LR
    UC4[Upload tài liệu] -. include .-> UC4a[Chunk & Embed tự động]
    UC4a -. include .-> UC4b[Lưu vector vào ChromaDB]
    UC7[Chat hỏi đáp] -. include .-> UC7a[Retrieve chunks liên quan]
    UC7 -. include .-> UC8[Trích dẫn nguồn]
    UC7 -. extend .-> UC7b[Trả lời 'Không có trong tài liệu']
```

> **Phân quyền tóm tắt:** User = chat + xem; Lecturer = User + quản lý tài liệu/môn học của mình; Admin = toàn quyền + quản lý người dùng + cấu hình.

---

## 2. Class Diagram (UML — Domain Model)

```mermaid
classDiagram
    class User {
        +int id
        +str email
        +str password_hash
        +str full_name
        +Role role
        +datetime created_at
    }
    class Role {
        <<enumeration>>
        ADMIN
        LECTURER
        USER
    }
    class Course {
        +int id
        +str name
        +str description
        +int owner_id
    }
    class Chapter {
        +int id
        +int course_id
        +str title
        +int order
    }
    class Document {
        +int id
        +int course_id
        +int chapter_id
        +int uploaded_by
        +str filename
        +FileType file_type
        +Status status
        +int num_chunks
        +datetime created_at
    }
    class FileType {
        <<enumeration>>
        PDF
        DOCX
        PPTX
    }
    class Status {
        <<enumeration>>
        PROCESSING
        INDEXED
        FAILED
    }
    class ChatSession {
        +int id
        +int user_id
        +str title
        +datetime created_at
    }
    class Message {
        +int id
        +int session_id
        +MsgRole role
        +str content
        +json citations
        +datetime created_at
    }
    class Citation {
        +str source_text
        +str document_name
        +int page
        +float score
    }

    User "1" --> "0..*" Course : owns (Lecturer)
    User "1" --> "0..*" Document : uploads
    User "1" --> "0..*" ChatSession : has
    Course "1" --> "0..*" Chapter
    Course "1" --> "0..*" Document
    Chapter "1" --> "0..*" Document
    ChatSession "1" --> "0..*" Message
    Message "1" --> "0..*" Citation : contains
    User --> Role
    Document --> FileType
    Document --> Status
```

---

## 3. Class Diagram (UML — Lớp ứng dụng theo Module)

```mermaid
classDiagram
    class DocumentRouter {
        +upload(file, course_id)
        +list()
        +delete(id)
    }
    class DocumentService {
        -repo: DocumentRepository
        -rag: RagFacade
        +ingest(file, course_id) Document
        +list_documents() list
    }
    class DocumentRepository {
        +create(doc) Document
        +get_all() list
        +update_status(id, status)
    }
    class Parser {
        <<interface>>
        +parse(file) str
    }
    class PdfParser
    class DocxParser
    class PptxParser

    class ChatRouter {
        +ask(question, session_id)
        +get_sessions()
    }
    class ChatService {
        -repo: ChatRepository
        -rag: RagFacade
        -llm: LlmClient
        +answer(q, session_id) ChatResponse
    }
    class RagFacade {
        -embedder: Embedder
        -store: VectorStore
        +index_chunks(chunks)
        +retrieve(query, k) list~Citation~
    }
    class Embedder {
        +embed(texts) list
    }
    class VectorStore {
        +add(vectors, meta)
        +query(vector, k) list
    }
    class LlmClient {
        +chat(messages) str
    }

    DocumentRouter --> DocumentService
    DocumentService --> DocumentRepository
    DocumentService --> RagFacade
    DocumentService --> Parser
    Parser <|.. PdfParser
    Parser <|.. DocxParser
    Parser <|.. PptxParser
    ChatRouter --> ChatService
    ChatService --> RagFacade
    ChatService --> LlmClient
    RagFacade --> Embedder
    RagFacade --> VectorStore
```

---

## 4. Sequence Diagram — Upload & Ingest tài liệu (Lecturer/Admin)

```mermaid
sequenceDiagram
    actor L as Lecturer
    participant FE as React UI
    participant R as DocumentRouter
    participant S as DocumentService
    participant P as Parser (Strategy)
    participant RAG as RagFacade
    participant E as Google Embedding
    participant C as ChromaDB
    participant DB as SQLite

    L->>FE: Chọn file + môn học
    FE->>R: POST /api/documents (file)
    R->>S: ingest(file, course_id)
    S->>DB: create Document (status=PROCESSING)
    S->>P: parse(file)
    P-->>S: text
    S->>S: chunk(text)
    S->>RAG: index_chunks(chunks)
    RAG->>E: embed(chunks)
    E-->>RAG: vectors
    RAG->>C: add(vectors, metadata)
    S->>DB: update status=INDEXED, num_chunks
    S-->>R: Document
    R-->>FE: 201 Created
    FE-->>L: Hiển thị "Đã index xong"
```

---

## 5. Sequence Diagram — Chat hỏi đáp (RAG Query)

```mermaid
sequenceDiagram
    actor U as User
    participant FE as React UI
    participant R as ChatRouter
    participant S as ChatService
    participant RAG as RagFacade
    participant E as Google Embedding
    participant C as ChromaDB
    participant LLM as Google Gemini 2.5 Flash
    participant DB as SQLite

    U->>FE: Nhập câu hỏi
    FE->>R: POST /api/chat {question, session_id}
    R->>S: answer(question, session_id)
    S->>DB: lấy lịch sử hội thoại
    S->>S: condense -> standalone question
    S->>RAG: retrieve(question, k=4)
    RAG->>E: embed(question)
    E-->>RAG: query_vector
    RAG->>C: query(query_vector, k=4, filter course_id)
    C-->>RAG: top chunks + metadata
    RAG-->>S: citations
    S->>LLM: chat(system + context + history + question)
    LLM-->>S: answer
    alt Không có thông tin trong context
        S-->>R: "Không tìm thấy trong tài liệu"
    else Có thông tin
        S->>DB: lưu user + assistant message
        S-->>R: {answer, citations}
    end
    R-->>FE: ChatResponse
    FE-->>U: Hiển thị câu trả lời + nguồn trích dẫn
```

---

## 6. Component / Architecture Diagram (Modular Monolith)

```mermaid
graph TB
    subgraph Client["🖥️ Frontend — React (Vite + TS + Tailwind)"]
        CP[ChatPage]
        DP[DocumentsPage]
        AP[Admin / Users Page]
    end

    subgraph Backend["⚙️ Backend — FastAPI (Modular Monolith, 1 process)"]
        direction TB
        API[API Layer / Routers + CORS]

        subgraph Modules["Business Modules"]
            AUTH[auth]
            USERS[users]
            DOCS[documents]
            COURSES[courses]
            CHAT[chat]
        end

        subgraph Shared["Shared Services"]
            RAG[rag: Embedder + Retriever + VectorStore Facade]
            LLMW[llm: Google Gemini client]
        end
    end

    subgraph Data["💾 Data Stores"]
        SQLITE[(SQLite — metadata)]
        CHROMA[(ChromaDB — vectors)]
    end

    subgraph External["☁️ External"]
        GEMINI[Google Gemini API]
    end

    Client -->|REST /api| API
    API --> AUTH & USERS & DOCS & COURSES & CHAT
    DOCS --> RAG
    CHAT --> RAG
    CHAT --> LLMW
    AUTH --> USERS
    DOCS --> SQLITE
    USERS --> SQLITE
    COURSES --> SQLITE
    CHAT --> SQLITE
    RAG --> CHROMA
    RAG --> GEMINI
    LLMW --> GEMINI
```

---

## 7. Design Patterns

```mermaid
graph TB
    subgraph "Patterns áp dụng"
        P1["Layered / Repository<br/>Router → Service → Repository"]
        P2["Strategy<br/>Parser chọn theo file type"]
        P3["Facade<br/>RagFacade che giấu Embedder/Store/Retriever"]
        P4["Dependency Injection<br/>FastAPI Depends inject service/repo"]
        P5["DTO<br/>Pydantic schemas tách model DB & API"]
        P6["Pipeline<br/>Ingest & Query là chuỗi bước"]
    end
```

| Pattern | Vấn đề giải quyết | Áp dụng |
|---------|-------------------|---------|
| **Layered / Repository** | Tách biệt HTTP / nghiệp vụ / dữ liệu | Mọi module |
| **Strategy** | Xử lý nhiều định dạng file khác nhau | `parsers.py` (PDF/DOCX/PPTX) |
| **Facade** | Đơn giản hóa subsystem RAG phức tạp | `rag/` module |
| **Dependency Injection** | Loose coupling, dễ test | FastAPI `Depends` |
| **DTO** | Tách API contract khỏi DB schema | Pydantic schemas |
| **Pipeline** | Chuỗi xử lý tuần tự rõ ràng | RAG ingest & query |
| **RBAC (Role-Based Access)** | Phân quyền 3 actor | `require_role()` dependency |

---

## 8. Deployment View

```mermaid
graph LR
    Browser[Trình duyệt] -->|HTTPS| Static[React build / Static host]
    Browser -->|REST API| FastAPI[FastAPI process]
    FastAPI --> Files[(File system:<br/>app.db + chroma/)]
    FastAPI -->|HTTPS| GEMINI[Google Gemini API]
```

Toàn bộ backend chạy trong **một process** (đúng tinh thần Modular Monolith). Dữ liệu lưu local (SQLite file + ChromaDB persistent dir). Có thể đóng gói Docker 1 container backend + 1 static frontend.

---

## 9. ERD — Lược đồ quan hệ dữ liệu (SQLite)

```mermaid
erDiagram
    USER ||--o{ COURSE : "owns (Lecturer)"
    USER ||--o{ DOCUMENT : uploads
    USER ||--o{ CHATSESSION : has
    COURSE ||--o{ CHAPTER : contains
    COURSE ||--o{ DOCUMENT : groups
    CHAPTER ||--o{ DOCUMENT : "optional"
    CHATSESSION ||--o{ MESSAGE : contains

    USER {
        int id PK
        string email UK
        string password_hash
        string full_name
        enum role "ADMIN|LECTURER|USER"
        datetime created_at
    }
    COURSE {
        int id PK
        string name
        string description
        int owner_id FK
    }
    CHAPTER {
        int id PK
        int course_id FK
        string title
        int order
    }
    DOCUMENT {
        int id PK
        int course_id FK
        int chapter_id FK "nullable"
        int uploaded_by FK
        string filename
        enum file_type "PDF|DOCX|PPTX"
        enum status "PROCESSING|INDEXED|FAILED"
        int num_chunks
        datetime created_at
    }
    CHATSESSION {
        int id PK
        int user_id FK
        string title
        datetime created_at
    }
    MESSAGE {
        int id PK
        int session_id FK
        enum role "user|assistant"
        string content
        json citations_json
        datetime created_at
    }
```

> Vector + chunk text **không** lưu trong SQLite mà nằm trong ChromaDB, kèm metadata `{document_id, course_id, chapter, chunk_index, source_text, page}`.

---

## 10. State Diagram — Vòng đời tài liệu (Document)

```mermaid
stateDiagram-v2
    [*] --> PROCESSING : upload (lưu metadata)
    PROCESSING --> INDEXED : parse + chunk + embed thành công
    PROCESSING --> FAILED : lỗi parse / embed (quota, định dạng)
    FAILED --> PROCESSING : upload lại
    INDEXED --> [*] : xóa tài liệu (kèm vector trong ChromaDB)
    FAILED --> [*] : xóa tài liệu
```

---

## 11. Activity Diagram — Luồng xử lý câu hỏi (RAG Query)

```mermaid
flowchart TD
    A([User gửi câu hỏi]) --> B[Lấy lịch sử hội thoại của phiên]
    B --> C{Có lịch sử?}
    C -- Có --> D[Condense: gộp lịch sử + câu hỏi<br/>thành standalone question]
    C -- Không --> E[Dùng nguyên câu hỏi]
    D --> F[Embed câu hỏi → query vector]
    E --> F
    F --> G[Similarity search ChromaDB<br/>top-k=4, filter theo course_id]
    G --> H{Có chunk liên quan?}
    H -- Không --> I[Trả lời: 'Không tìm thấy trong tài liệu']
    H -- Có --> J[Build prompt:<br/>system + context + history + câu hỏi]
    J --> K[Gọi Gemini LLM]
    K --> L[Sinh câu trả lời + gắn citations]
    L --> M[Lưu user + assistant message vào phiên]
    I --> M
    M --> N([Trả về answer + citations cho UI])
```

---

## 12. Package / Module Diagram (cấu trúc backend)

```mermaid
graph TD
    MAIN[app.main<br/>FastAPI app, mount routers, CORS]
    CONFIG[app.config<br/>Settings từ .env]
    DB[app.database<br/>SQLAlchemy engine/session]
    SHARED[app.shared<br/>exceptions, dependencies, require_role]

    subgraph modules
        AUTH[auth]
        USERS[users]
        COURSES[courses]
        DOCUMENTS[documents]
        CHAT[chat]
        RAG[rag]
    end
    LLM[app.llm<br/>Gemini client]

    MAIN --> AUTH & USERS & COURSES & DOCUMENTS & CHAT
    MAIN --> CONFIG
    AUTH --> USERS
    AUTH --> SHARED
    USERS --> DB
    COURSES --> DB
    DOCUMENTS --> DB
    DOCUMENTS --> RAG
    DOCUMENTS --> SHARED
    CHAT --> DB
    CHAT --> RAG
    CHAT --> LLM
    CHAT --> SHARED
    RAG --> LLM
    RAG --> CONFIG
    LLM --> CONFIG
```
