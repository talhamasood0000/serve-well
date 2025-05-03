from collections import defaultdict


def refine_sentiment(original_sentiment, emotions):
    positive = {"satisfaction", "joy", "relief", "gratitude"}
    negative = {"disappointment", "frustration", "anger", "sadness"}
    has_pos = any(e in positive for e in emotions)
    has_neg = any(e in negative for e in emotions)

    if has_pos and has_neg:
        return "mixed"
    elif has_pos:
        return "positive"
    elif has_neg:
        return "negative"
    return original_sentiment or "neutral"


def create_conversation(questions):
    conversation = ""
    for entry in questions:
        conversation += f"Agent: {entry['questions__question']}\n"
        conversation += f"Customer: {entry['questions__answer']}\n\n"
    
    return conversation


def re_structure_orders(orders):
    orders_dict = defaultdict(list)

    for order in orders:
        orders_dict[order["id"]].append(order)

    for key in orders_dict:
        orders_dict[key].sort(key=lambda d: d["questions__priority"])

    return orders_dict
