{
    'name' : 'Inventory and Stock Aging Report for Warehouse',
    'author': "Edge Technologies",
    'version' : '15.0.1.0',
    'live_test_url':'https://youtu.be/69n5iyMfHYg',
    "images":["static/description/main_screenshot.png"],
    'summary' : 'Product Stock Aging Reports Inventory Aging Report warehouse Aging Report product Aging Report for stock expiry report inventory expiry report stock overdue stock report due stock report product due report stock overdate report overdate stock reports',
    'description' : """
        Stock Inventory Aging Report Filter by Product, Category, Location, Warehouse, Date, and Period Length.
    """,
    'depends' : ['base','sale_management','purchase','stock'],
    "license" : "OPL-1",
    'data': [
            'security/ir.model.access.csv',
            'wizard/stock_aging_report_view.xml',
            'report/stock_aging_report.xml',
            'report/stock_aging_report_template.xml',
            ],
    'qweb' : [],
    'demo' : [],
    'installable' : True,
    'auto_install' : False,
    'price': 20,
    'currency': "EUR",
    'category' : 'Warehouse',
}
