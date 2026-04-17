from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from setting.config import settings
from db.database import get_db
from sqlalchemy.orm import Session
from db import models
import os
import json
import traceback

# from langchain_google_genai import ChatGoogleGenerativeAI  # Gemini
from langchain_openai import ChatOpenAI  # OpenAI ChatGPT
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.chains import create_retrieval_chain
from setting.utils import get_current_user

router = APIRouter(prefix="/chatbot", tags=["Chatbot AI RAG"])


class ChatRequest(BaseModel):
    message: str


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class RecommendRequest(BaseModel):
    message: str
    chat_history: Optional[List[ChatMessage]] = None


class ServiceRecommendation(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    price: Optional[float] = None
    duration: Optional[int] = None
    images: Optional[List[str]] = None


class RecommendResponse(BaseModel):
    answer: str
    recommended_services: List[ServiceRecommendation] = []


# Global instances cache
retrieval_chain = None
llm_instance = None


def init_rag():
    global retrieval_chain, llm_instance
    # === Gemini  ===
    # if not settings.GOOGLE_API_KEY:
    #     print("WARNING: GOOGLE_API_KEY is not set in environment or config.")
    #     return
    # === OpenAI  ===
    if not settings.OPENAI_API_KEY:
        print("WARNING: OPENAI_API_KEY is not set in environment or config.")
        return

    try:
        # === Gemini  ===
        # os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY
        # gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        # llm_instance = ChatGoogleGenerativeAI(model=gemini_model, temperature=0.7)
        # print(f"Using Gemini model: {gemini_model}")

        # === OpenAI ChatGPT  ===
        os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
        openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        llm_instance = ChatOpenAI(model=openai_model, temperature=0.7)
        print(f"Using OpenAI model: {openai_model}")

        # 2. Embedding Model
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

        # 3. Load local FAISS vector store
        faiss_path = "faiss_index"
        if os.path.exists(faiss_path):
            vector_store = FAISS.load_local(
                faiss_path, embeddings, allow_dangerous_deserialization=True
            )
            retriever = vector_store.as_retriever(search_kwargs={"k": 3})

            # 4. Formulate the RAG Prompt
            prompt_template = ChatPromptTemplate.from_template(
                "Bạn là trợ lý ảo chuyên nghiệp của phòng khám thú y Coco Pet.\n"
                "Sử dụng các thông tin ngữ cảnh sau đây để cung cấp lời khuyên chính xác, thân thiện.\n"
                "Quy định chung:\n"
                "- Giờ làm việc: 6:00 sáng - 10:00 tối (22:00) hàng ngày.\n"
                "- Tất cả dịch vụ có giá niêm yết cố định (không phân biệt cân nặng/giới tính).\n"
                "- Nếu thông tin không có trong ngữ cảnh, hãy từ chối lịch sự và khuyên liên hệ trực tiếp phòng khám qua số điện thoại 0909090909.\n\n"
                "Thông tin phòng khám & Kiến thức (Ngữ cảnh):\n{context}\n\n"
                "Khách hàng: {input}\n"
                "Trợ lý AI:"
            )

            document_chain = create_stuff_documents_chain(llm_instance, prompt_template)
            retrieval_chain = create_retrieval_chain(retriever, document_chain)
            print("Chatbot RAG (FAISS + Gemini) has successfully initialized!")
        else:
            print(
                "WARNING: faiss_index not found. Did you forget to run ingest_data.py?"
            )

    except Exception as e:
        print(f"Error initializing RAG Chatbot System: {e}")


# Auto Initialize when App loads the router
init_rag()


@router.post("/ask")
def chat_with_ai(req: ChatRequest):
    if not retrieval_chain:
        init_rag()
        if not retrieval_chain:
            raise HTTPException(
                status_code=503,
                detail="Hệ thống Chatbot RAG đang bảo trì hoặc đang khuyết dữ liệu/API Key.",
            )
    try:
        response = retrieval_chain.invoke({"input": req.message})
        return {"answer": response["answer"]}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Lỗi truy vấn AI: {str(e)}")


def _build_conversation_context(chat_history: Optional[List[ChatMessage]]) -> str:
    """Build conversation context string from chat history."""
    if not chat_history:
        return ""

    lines = []
    for msg in chat_history[-10:]:  # Keep last 10 messages for context
        role_label = "Khách hàng" if msg.role == "user" else "Trợ lý AI"
        lines.append(f"{role_label}: {msg.content}")

    return "\n".join(lines)


def _get_smart_recommendations(
    message: str, ai_answer: str, user_pets: List[models.Pet], db: Session
) -> List[dict]:
    """
    Use LLM reasoning to find best matching services based on context and user pets.
    """
    global llm_instance
    if not llm_instance:
        return []

    # Get all services
    all_services = db.query(models.Service).all()
    if not all_services:
        return []

    services_info = "\n".join(
        [f"- ID: {s.id}, Tên: {s.name}, Mô tả: {s.description}" for s in all_services]
    )
    pets_info = (
        ", ".join([f"{p.breed} ({p.name}, {p.age} tuổi)" for p in user_pets])
        if user_pets
        else "Chưa đăng ký thú cưng"
    )

    recommend_prompt = (
        f"Dựa trên tin nhắn của khách hàng: '{message}'\n"
        f"Và câu trả lời của AI: '{ai_answer}'\n"
        f"Cùng thông tin thú cưng của khách hàng: {pets_info}\n"
        f"Hãy chọn tối đa 3 dịch vụ phù hợp nhất từ danh sách sau:\n{services_info}\n\n"
        "Chỉ trả về danh sách các ID dịch vụ (ví dụ: [1, 2, 3]), nếu không có dịch vụ nào phù hợp hãy trả về []"
    )

    try:
        res = llm_instance.invoke(recommend_prompt)
        content = res.content.strip()
        # Simple extraction of list-like string
        if "[" in content and "]" in content:
            start = content.find("[")
            end = content.find("]") + 1
            service_ids = json.loads(content[start:end])

            result = []
            for s_id in service_ids:
                service = (
                    db.query(models.Service).filter(models.Service.id == s_id).first()
                )
                if service:
                    images = [img.image_url for img in (service.images or [])]
                    result.append(
                        {
                            "id": service.id,
                            "name": service.name,
                            "description": service.description,
                            "icon": service.icon,
                            "price": float(service.price) if service.price else None,
                            "duration": service.duration,
                            "images": images,
                        }
                    )
            return result
    except Exception as e:
        print(f"Error in smart recommendation: {e}")
        traceback.print_exc()
        # Fallback to current simple matching if AI fails
        return []

    return []


@router.post("/recommend", response_model=RecommendResponse)
def chat_with_recommendation(
    req: RecommendRequest,
    db_info=Depends(get_current_user),
):
    """
    Conversational chatbot with service recommendation.
    Accepts chat_history for conversation memory.
    Returns AI answer + recommended_services if relevant.
    """
    db, user_data, _ = db_info
    if not retrieval_chain:
        init_rag()
        if not retrieval_chain:
            raise HTTPException(
                status_code=503,
                detail="Hệ thống Chatbot RAG đang bảo trì hoặc đang khuyết dữ liệu/API Key.",
            )

    try:
        # Build conversation context
        history_context = _build_conversation_context(req.chat_history)

        # Fetch user pets for context
        user_id = user_data["user_id"]
        pets = (
            db.query(models.Pet)
            .filter(models.Pet.user_id == user_id, models.Pet.is_deleted == False)
            .all()
        )
        pets_context = "Thông tin thú cưng của khách hàng: " + (
            ", ".join([f"{p.breed} ({p.name})" for p in pets])
            if pets
            else "Chưa có thú cưng."
        )

        # Construct input with conversation history and pet context
        full_input = f"[{pets_context}]\n"
        if history_context:
            full_input += f"Lịch sử hội thoại trước đó:\n{history_context}\n\n"

        full_input += f"Câu hỏi mới nhất: {req.message}"

        # Get RAG response
        response = retrieval_chain.invoke({"input": full_input})
        ai_answer = response["answer"]

        # Find smart matching services from DB (with fallback)
        recommended_services = []
        try:
            recommended_services = _get_smart_recommendations(
                req.message, ai_answer, pets, db
            )
        except Exception as rec_err:
            print(
                f"Recommendation failed (non-fatal, returning answer only): {rec_err}"
            )

        return RecommendResponse(
            answer=ai_answer,
            recommended_services=recommended_services,
        )

    except Exception as e:
        traceback.print_exc()
        error_msg = str(e)
        # Check for quota/rate limit errors
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            raise HTTPException(
                status_code=429,
                detail="Hệ thống AI đang quá tải. Vui lòng thử lại sau vài giây.",
            )
        raise HTTPException(status_code=500, detail=f"Lỗi truy vấn AI: {error_msg}")
