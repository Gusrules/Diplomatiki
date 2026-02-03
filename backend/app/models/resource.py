from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from app.db_base import Base


class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)

    # Το resource ανήκει σε μία ενότητα (module)
    module_id = Column(Integer, ForeignKey("modules.id", ondelete="CASCADE"), nullable=False)

    # Τύπος υλικού (οι τιμές που συμφωνήσαμε)
    type = Column(String(20), nullable=False)  # 'study_guide', 'flashcard', 'explanation'

    # Τίτλος που θα φαίνεται στο UI
    title = Column(String(150), nullable=False)

    # ΔΕΝ αποθηκεύουμε το αρχείο στη βάση -> κρατάμε path στο filesystem
    file_path = Column(Text, nullable=False)

    # Π.χ. pdf, docx, txt, json
    file_type = Column(String(10), nullable=False)

    # Ποιος καθηγητής το ανέβασε
    uploaded_by = Column(Integer, ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    content = Column(Text, nullable=True)
