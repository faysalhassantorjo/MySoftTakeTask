how to run the project?
clone the repository
run 
```bash
docker compose build
```
```bash
docker compose up
```

then open http://127.0.0.1:8000 in your browser

Guidline
1. http://127.0.0.1:8000/api/create-products/
    - you can create products - List of products

2. http://127.0.0.1:8000/api/reservation/
    - POST /api/reservations/ creates reservation for 10 minute
        - reserved_stock using `Transaction`
        - used celery `background` task to update reservation after 10 minute - it will update status as `expired` and restore the product stock
    - implemented `celery-beat` for reservation cleanup - preodic

3. http://127.0.0.1:8000/api/create-order/
    - POST /api/orders/ creates order
    - you can also create Order Item
        -  crate orderItem (here orderitem price and quantity just for the demo for Sorting and filtering Purposes)

4. http://127.0.0.1:8000/api/order-list/
    - GET /api/orders/ must support:
        - filter: date range, status, min/max total
        - sort: newest, highest value
        - cursor pagination
    
    ![alt text](image.png)

5. http://127.0.0.1:8000/api/order/<int:pk>/
    - GET /api/orders/<int:pk>/ updates order
    - you can update order status but only if the current status is allowed to transition to the new status

    ![alt text](image-1.png)

6. execute the `chaostest.py` file to test the concurrency
    - You will see the result in the terminal
    ![alt text](image-2.png)



## Task 1
- Created Product model
- Created Reservation model
- POST /api/reservations/ creates reservation for 10 minute
    - reserved_stock using `Transaction`
    - used celery `background` task to update reservation after 10 minute
- implemented `celery-beat` for reservation cleanup 


## Task 2:
- set up some rules for order status transition
- then only used on if condition to check that the current status is allowed to transition to the new status, if YES then update the status

## Task 3
- for the concurrency i used `Celery` with Redis as Broker not the Thread
        it will take 50 parallel Purchases attempts at a time and execute them parallelly
    
  for the chaos test i used the chaostest.py file
    ```bash
    job = group(attempt_purchase_task.s(product.id) for _ in range(50))
    result = job.apply_async()
    outputs = result.get()
    ```
  to send the requests parallelly i used the group function and got the result at once
    [here is the picture]
    
    

## Task 4
GET /api/orders/ must support:
    - filter: date range, status, min/max total
    - sort: newest, highest value
    - cursor pagination
    
for the filter i used django-filter and created a Custom Class
- then used the class in the OrderListView
- and for the pagination i used cursor pagination

and for the databse indexing i indexed user, created_at, status
- user will be the frequently searched field, 
- created_at will be the frequently sorted field,
- and status will be the frequently filtered field
thats why i indexed them, indexing will use B-Tree search, it will be fast but use more space, thats why i  indexed only the frequently used fields

- for the cursor pagination rest_framework pagination is used
- and use select related becasue i have a foreign key relationship with user model. and it will reduce the number of queries if i had more than one foreign key relationship, but in this case i only have one        foreign key relationship. So it will only fetch the user data in the same query


Task 5:
    - for the audit log i used signals and manually created the audit log


Task 6:
  1. crash recovery after reservation
    - No data missmatch due to atomic transaction, all or nothing (rollback)
    - Store reservation in persistant db so that if server crash after recovery the data are safe and 
 

  3. cleanup strategy + frequency
    - i am using celery beat to cleanup the reservation after 10 minutes
   
  4. multi-warehouse design choices
     will cerate multiple Werehouse. 
    