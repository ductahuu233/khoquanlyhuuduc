import os
import sys
from app.database import engine, Base, SessionLocal
from app.models import User, Item, Request, RequestDetail, Transaction

def test_database_setup():
    print("=== STARTING PHASE 1 DATABASE TEST ===")
    
    # 1. Initialize Tables
    print("1. Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    db_file = "database.db"
    assert os.path.exists(db_file), f"Error: {db_file} was not created!"
    print(f"   [PASS] {db_file} file verified on disk.")

    db = SessionLocal()
    try:
        # Clear any existing data for a clean test
        db.query(Transaction).delete()
        db.query(RequestDetail).delete()
        db.query(Request).delete()
        db.query(Item).delete()
        db.query(User).delete()
        db.commit()

        # 2. Test User Model
        print("2. Testing User model insertion...")
        admin = User(username="admin_user", role="admin")
        keeper = User(username="store_keeper_1", role="storekeeper")
        db.add_all([admin, keeper])
        db.commit()
        
        users_count = db.query(User).count()
        assert users_count == 2, f"Expected 2 users, got {users_count}"
        print(f"   [PASS] Created {users_count} users successfully.")

        # 3. Test Item Model
        print("3. Testing Item model insertion...")
        item1 = Item(item_code="VT001", name="Máy in HP LaserJet", unit="Cái", current_stock=10)
        item2 = Item(item_code="VT002", name="Giấy A4 Double A 70gsm", unit="Ram", current_stock=50)
        db.add_all([item1, item2])
        db.commit()

        items_count = db.query(Item).count()
        assert items_count == 2, f"Expected 2 items, got {items_count}"
        print(f"   [PASS] Created {items_count} items successfully.")

        # 4. Test Request & RequestDetail Models
        print("4. Testing Request & RequestDetail models...")
        req = Request(requester_name="Nguyễn Văn A", status="pending")
        db.add(req)
        db.commit()
        db.refresh(req)

        detail1 = RequestDetail(request_id=req.id, item_id=item1.id, quantity=2)
        detail2 = RequestDetail(request_id=req.id, item_id=item2.id, quantity=5)
        db.add_all([detail1, detail2])
        db.commit()

        fetched_req = db.query(Request).filter(Request.id == req.id).first()
        assert fetched_req is not None
        assert len(fetched_req.details) == 2
        print(f"   [PASS] Request #{fetched_req.id} created with {len(fetched_req.details)} detail items.")

        # 5. Test Transaction Model
        print("5. Testing Transaction model...")
        trans = Transaction(request_id=req.id, item_id=item1.id, type="OUT", quantity=2)
        db.add(trans)
        db.commit()

        trans_count = db.query(Transaction).count()
        assert trans_count == 1
        print(f"   [PASS] Transaction log created successfully.")

        print("\n=== PHASE 1 TEST PASSED SUCCESSFULLY! ===")
    except Exception as e:
        print(f"\n[FAIL] Phase 1 test encountered an error: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    test_database_setup()
