def rent_scooter(scooter_id: str, payment_info: dict, user_id: str):
    if not is_scooter_available(scooter_id):
        raise ScooterUnavailableError("Scooter is already in use.")

    if not process_payment(payment_info):
        raise PaymentFailedError("Payment could not be completed.")

    unlock_scooter(scooter_id)
    notify_user(user_id, "Scooter unlocked successfully.")
