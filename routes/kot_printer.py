from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta, date
import json
from io import BytesIO

# Import ReportLab for PDF generation
try:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.units import cm, mm
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

routes = APIRouter(prefix="/kots", tags=["KOT Printer"])

# ═══════════════════════════════════════════════════════════════════════════
# GET KOT by ID
# ═══════════════════════════════════════════════════════════════════════════
@routes.get("/{kot_id}")
async def get_kot(kot_id: str, db):
    """Get specific KOT details"""
    try:
        from models import KOT
        kot = db.query(KOT).filter(KOT.id == kot_id).first()
        if not kot:
            raise HTTPException(status_code=404, detail="KOT not found")
        return kot
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching KOT: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════
# UPDATE KOT Status
# ═══════════════════════════════════════════════════════════════════════════
@routes.put("/{kot_id}")
async def update_kot_status(kot_id: str, data: dict):
    """Update KOT status (pending → printed → dispatched)"""
    try:
        from models import KOT
        
        kot = db.query(KOT).filter(KOT.id == kot_id).first()
        if not kot:
            raise HTTPException(status_code=404, detail="KOT not found")

        if 'status' in data:
            valid_statuses = ['pending', 'printed', 'dispatched', 'completed']
            if data['status'] not in valid_statuses:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                )
            
            kot.status = data['status']
            kot.updated_at = datetime.now()

        db.commit()
        db.refresh(kot)
        
        return {
            "message": f"KOT status updated to {data.get('status')}",
            "kot_id": kot.id,
            "status": kot.status,
            "updated_at": kot.updated_at
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating KOT: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════
# GENERATE KOT PDF
# ═══════════════════════════════════════════════════════════════════════════
@routes.post("/{kot_id}/generate-pdf")
async def generate_kot_pdf(kot_id: str):
    """Generate PDF of KOT for printing"""
    if not REPORTLAB_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="PDF generation library not installed. Run: pip install reportlab"
        )
    
    try:
        from models import KOT
        
        kot = db.query(KOT).filter(KOT.id == kot_id).first()
        if not kot:
            raise HTTPException(status_code=404, detail="KOT not found")

        buffer = BytesIO()
        page_width = 80 * mm
        page_height = 200 * mm
        
        pdf_canvas = canvas.Canvas(buffer, pagesize=(page_width, page_height))
        
        pdf_canvas.setFont("Helvetica-Bold", 12)
        y_position = page_height - 15 * mm
        
        pdf_canvas.drawCentredString(page_width / 2, y_position, "TASTE PARADISE")
        y_position -= 5 * mm
        
        pdf_canvas.setFont("Helvetica", 9)
        pdf_canvas.drawCentredString(page_width / 2, y_position, "Kitchen Order Ticket")
        y_position -= 5 * mm
        
        pdf_canvas.line(5 * mm, y_position, page_width - 5 * mm, y_position)
        y_position -= 4 * mm
        
        pdf_canvas.setFont("Helvetica-Bold", 8)
        details = [
            f"Order ID: {kot.order_id}",
            f"KOT ID: {kot.id[:8]}",
            f"Table: {getattr(kot, 'table_number', 'N/A') or 'N/A'}",
            f"Time: {kot.created_at.strftime('%H:%M')}" if hasattr(kot, 'created_at') else "Time: N/A"
        ]
        
        for detail in details:
            pdf_canvas.drawString(7 * mm, y_position, detail)
            y_position -= 3 * mm
        
        y_position -= 2 * mm
        pdf_canvas.line(5 * mm, y_position, page_width - 5 * mm, y_position)
        y_position -= 4 * mm
        
        pdf_canvas.setFont("Helvetica-Bold", 9)
        pdf_canvas.drawString(7 * mm, y_position, "ORDER ITEMS")
        y_position -= 3 * mm
        
        pdf_canvas.setFont("Helvetica", 8)
        
        if hasattr(kot, 'items') and kot.items:
            try:
                items_data = json.loads(kot.items) if isinstance(kot.items, str) else kot.items
            except:
                items_data = []
            
            for item in items_data:
                item_name = item.get('name', 'Item')
                quantity = item.get('quantity', 1)
                notes = item.get('notes', '')
                
                item_text = f"{quantity}x {item_name}"
                if notes:
                    item_text += f" ({notes})"
                
                pdf_canvas.drawString(10 * mm, y_position, item_text)
                y_position -= 3 * mm
        
        if hasattr(kot, 'special_instructions') and kot.special_instructions:
            y_position -= 2 * mm
            pdf_canvas.line(5 * mm, y_position, page_width - 5 * mm, y_position)
            y_position -= 4 * mm
            
            pdf_canvas.setFont("Helvetica-Bold", 8)
            pdf_canvas.drawString(7 * mm, y_position, "SPECIAL INSTRUCTIONS:")
            y_position -= 3 * mm
            
            pdf_canvas.setFont("Helvetica", 7)
            instructions = kot.special_instructions.split('\\n')
            for instruction in instructions:
                pdf_canvas.drawString(10 * mm, y_position, instruction[:40])
                y_position -= 2 * mm
        
        y_position -= 2 * mm
        pdf_canvas.line(5 * mm, y_position, page_width - 5 * mm, y_position)
        y_position -= 4 * mm
        
        pdf_canvas.setFont("Helvetica", 7)
        pdf_canvas.drawCentredString(page_width / 2, y_position, "Thank You!")
        
        pdf_canvas.save()
        
        kot.status = 'printed'
        kot.updated_at = datetime.now()
        db.commit()
        
        buffer.seek(0)
        return buffer.getvalue()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════
# GET PENDING KOTS
# ═══════════════════════════════════════════════════════════════════════════
@routes.get("/pending/list")
async def get_pending_kots():
    """Get all pending KOTs"""
    try:
        from models import KOT
        
        pending_kots = db.query(KOT).filter(
            KOT.status == 'pending'
        ).order_by(KOT.created_at.asc()).all()
        
        return {
            "count": len(pending_kots),
            "kots": pending_kots
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching pending KOTs: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════
# GET KOTS BY DATE
# ═══════════════════════════════════════════════════════════════════════════
@routes.get("/date/{date_str}")
async def get_kots_by_date(date_str: str):
    """Get all KOTs for a specific date (format: YYYY-MM-DD)"""
    try:
        from models import KOT
        
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_date = datetime.combine(date_obj, datetime.min.time())
        end_date = start_date + timedelta(days=1)
        
        kots = db.query(KOT).filter(
            and_(
                KOT.created_at >= start_date,
                KOT.created_at < end_date
            )
        ).order_by(KOT.created_at.desc()).all()
        
        return {
            "date": date_str,
            "count": len(kots),
            "kots": kots
        }
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching KOTs: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════
# GET KOTS BY STATUS
# ═══════════════════════════════════════════════════════════════════════════
@routes.get("/status/{status_filter}")
async def get_kots_by_status(status_filter: str):
    """Get all KOTs with specific status"""
    try:
        from models import KOT
        
        valid_statuses = ['pending', 'printed', 'dispatched', 'completed']
        if status_filter not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        kots = db.query(KOT).filter(
            KOT.status == status_filter
        ).order_by(KOT.created_at.desc()).all()
        
        return {
            "status": status_filter,
            "count": len(kots),
            "kots": kots
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching KOTs: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════
# GET KOT STATISTICS
# ═══════════════════════════════════════════════════════════════════════════
@routes.get("/stats/daily")
async def get_kot_stats():
    """Get KOT statistics for today"""
    try:
        from models import KOT
        
        today = datetime.now().date()
        start_date = datetime.combine(today, datetime.min.time())
        end_date = start_date + timedelta(days=1)
        
        total = db.query(KOT).filter(
            and_(KOT.created_at >= start_date, KOT.created_at < end_date)
        ).count()
        
        pending = db.query(KOT).filter(
            and_(
                KOT.created_at >= start_date,
                KOT.created_at < end_date,
                KOT.status == 'pending'
            )
        ).count()
        
        printed = db.query(KOT).filter(
            and_(
                KOT.created_at >= start_date,
                KOT.created_at < end_date,
                KOT.status == 'printed'
            )
        ).count()
        
        return {
            "date": str(today),
            "total_kots": total,
            "pending": pending,
            "printed": printed,
            "dispatched": total - pending - printed
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching statistics: {str(e)}")