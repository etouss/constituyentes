from sqlalchemy.sql import text

def register_feedback(tx_id, question, answer, user_feedback, db):
    try:
        db.execute(
            text(
            "INSERT INTO feedback(tx_id, question, answer, user_feedback) "
            "VALUES (:tx_id, :question, :answer, :user_feedback)"),
            {
                "tx_id": tx_id,
                "question": question,
                "answer": answer,
                "user_feedback": user_feedback
            }
        )
        db.commit()
    except Exception as e:
        print("### Error: register_feedback ###")
        print(e)
        db.rollback()
