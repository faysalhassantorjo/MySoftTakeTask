

def confirm_reserved_stock(order):
    for item in order.items.select_for_update():
        product = item.product
        product.reserved_stock -= item.quantity
        product.sold_stock += item.quantity
        product.save()
def release_reserved_stock(order):
    for item in order.items.select_for_update():
        product = item.product
        product.reserved_stock -= item.quantity
        product.available_stock += item.quantity
        product.save()
