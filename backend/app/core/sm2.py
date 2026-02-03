from datetime import date, timedelta

# ------------------------
# SM-2 core algorithm
# Βασισμένο στο κείμενο της Ανάλυσης Απαιτήσεων:
# Αν q = 0:
#   repetitions = 0
#   interval = 1
#   EF = EF - 0.3 (min 1.3)
# Αν q = 1:
#   repetitions += 1
#   αν repetitions = 1 -> interval = 2
#   αν repetitions = 2 -> interval = 6
#   αν repetitions >= 3 -> interval = round(interval * EF)
#   EF = EF + 0.1
# ------------------------

def sm2_update(ef: float, repetitions: int, interval: int, quality: int):
    """
    Επιστρέφει: (new_ef, new_repetitions, new_interval, next_review_date)
    """
    if quality not in (0, 1):
        raise ValueError("quality πρέπει να είναι 0 (λάθος) ή 1 (σωστό)")

    if quality == 0:
        repetitions = 0
        interval = 1  # ξαναβλέπουμε την ερώτηση αύριο
        ef = max(1.3, ef - 0.3)
    else:  # quality == 1
        repetitions += 1
        if repetitions == 1:
            interval = 2
        elif repetitions == 2:
            interval = 6
        else:
            interval = round(interval * ef)

        ef = ef + 0.1

    next_review = date.today() + timedelta(days=interval)
    return ef, repetitions, interval, next_review


# ------------------------
# Προσαρμογή δυσκολίας ερώτησης (difficulty_score)
# ------------------------

def update_difficulty_score(current: float, quality: int) -> float:
    """
    Απλή προσαρμογή:
    - σωστή απάντηση -> ερώτηση θεωρείται λίγο πιο εύκολη
    - λάθος απάντηση -> ερώτηση θεωρείται λίγο πιο δύσκολη
    Κρατάμε πάντα στο [0.0, 10.0]
    """
    if quality == 1:
        new_score = max(0.0, current - 0.2)
    else:
        new_score = min(10.0, current + 0.3)
    return new_score


# ------------------------
# Προσαρμογή επιπέδου φοιτητή (user_level.level)
# με βάση το συνολικό σκορ του quiz
# ------------------------

def update_user_level(current_level: float, score_ratio: float) -> float:
    """
    score_ratio = correct / total (0.0 - 1.0)

    - Αν score >= 0.8 -> ανεβάζουμε level +0.5
    - Αν score <= 0.4 -> κατεβάζουμε level -0.3
    - Αλλιώς -> μικρή θετική προσαρμογή +0.1

    Κρατάμε πάντα στο [0.0, 10.0]
    """
    if score_ratio >= 0.8:
        current_level += 0.5
    elif score_ratio <= 0.4:
        current_level -= 0.3
    else:
        current_level += 0.1

    if current_level < 0.0:
        current_level = 0.0
    if current_level > 10.0:
        current_level = 10.0

    return current_level
