#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np
from collections import defaultdict
from ortools.linear_solver import pywraplp


# In[2]:




""" PART A: A. Load the input data from the file “supplychain_data.xlsx” [1 point]."""

filename="supplychain_data.xlsx"
Supplier_stock =           pd.read_excel(filename,     sheet_name="Supplier stock",              header=[0], index_col=[0])
Rawmaterial_costs  =       pd.read_excel(filename,     sheet_name="Raw material costs",          header=[0], index_col=[0])
Rawmaterial_shipping  =    pd.read_excel(filename,     sheet_name="Raw material shipping",       header=[0], index_col=[0])
Product_requirements =     pd.read_excel(filename,     sheet_name="Product requirements",        header=[0], index_col=[0])

Production_capacity    =   pd.read_excel(filename,     sheet_name="Production capacity",   header=[0], index_col=[0])
Production_cost  =         pd.read_excel(filename,     sheet_name="Production cost",       header=[0], index_col=[0])
Customer_demand =          pd.read_excel(filename,     sheet_name="Customer demand",       header=[0], index_col=[0])
Shipping_costs =           pd.read_excel(filename,     sheet_name="Shipping costs",        header=[0], index_col=[0])


# In[3]:


solver = pywraplp.Solver('supplychainoptimisation', pywraplp.Solver.GLOP_LINEAR_PROGRAMMING)
                             
infinity = solver.infinity()


# In[4]:


suppliers = list(Supplier_stock.index.values)
print(suppliers)

materials = list(Supplier_stock.columns.values)
print(materials)

products = list(Customer_demand.index.values)
print(products)

customers = list(Customer_demand.columns.values)
print(customers)


factories = list(Shipping_costs.index.values)
print(factories)



# In[5]:



""" PART  B - Identify and create the decision variables for the delivery to the customers [1 point] """
products_from_factories_to_customers = {}

for f in factories:
    for p in products:
        for c in customers:
            if not pd.isna(Production_capacity.loc[p,f]):
                products_from_factories_to_customers[(f,p,c)] = solver.IntVar(0,infinity,f+"_"+p+"_"+c+"_products_from_factories_to_customers")     
            else:
                products_from_factories_to_customers[(f,p,c)] = None
                

""" PART  B - Identify and create the decision variables for the orders from the suppliers [1 point] """
supplier_sent_material_to_fact = {}

for s in suppliers:
    for m in materials:
        for f in factories:
            if not pd.isna(Supplier_stock.loc[s,m]):
                supplier_sent_material_to_fact[(s,m,f)] = solver.IntVar(0,infinity,s+"_"+m+"_"+f+"_supplier_sent_material_to_fact")
            else:
                supplier_sent_material_to_fact[(s,m,f)] = None
                
                



# In[6]:



""" PART  C - Define and implement the constraints that ensure factories produce more than 
              they ship to the customers [2 points] """


""" PART  D - Define and implement the constraints that ensure that customer demand is met [2 points].  """
for c in customers:
    for p in products:
        if not pd.isna(Customer_demand.loc[p,c]):
            constraint=solver.Constraint(int(Customer_demand.loc[p,c]), infinity)
        
            for f in factories:
                if products_from_factories_to_customers[(f,p,c)] is not None:           
                    constraint.SetCoefficient(products_from_factories_to_customers[(f,p,c)],1)
            


# In[7]:




                
                
""" PART  E - Define and implement the constraints that ensure that suppliers have all ordered
              items in stock [2 points].  """

for s in suppliers:
    constraint = None
    for m in materials:  
        if not pd.isna(Supplier_stock.loc[s,m]):
            constraint=solver.Constraint(0,int(Supplier_stock.loc[s,m]))
        for f in factories:
            if supplier_sent_material_to_fact[(s,m,f)] is not None:
                constraint.SetCoefficient(supplier_sent_material_to_fact[(s,m,f)],1)
            


# In[8]:


""" PART  F - Define and implement the constraints that ensure that factories order enough material to be able to manufacture all items [2 points].   """

for f in factories:
    constraint = None
    for m in materials:        
        constraint=solver.Constraint(0,0)
        for s in suppliers:
            if supplier_sent_material_to_fact[(s,m,f)] is not None:
                constraint.SetCoefficient(supplier_sent_material_to_fact[(s,m,f)],1)
                
                for p in products:
                    if (not pd.isna(Product_requirements.loc[p,m] )) and (not pd.isna(Production_capacity.loc[p,f])):
                        for c in customers:
                            if products_from_factories_to_customers[(f,p,c)] is not None:
                                constraint.SetCoefficient( products_from_factories_to_customers[(f,p,c)] , -Product_requirements.loc[p,m])
                
                
                
                
                


# In[ ]:

""" PART  G - Define and implement the constraints that ensure that the manufacturing capacities are not exceeded [2 points].  """

for f in factories:
    for p in products:
        constraint = None
        if not pd.isna(Production_capacity.loc[p,f]):
            constraint=solver.Constraint(0,int(Production_capacity.loc[p,f]))
            for c in customers:
                if  products_from_factories_to_customers[(f,p,c)] is not None:     
                    constraint.SetCoefficient(products_from_factories_to_customers[(f,p,c)],1)
           





# In[9]:


""" PART  H - Define and implement the objective function.
              Make sure to consider the production cost of each factory [2 points], 
              and the cost of delivery to each customer [2 points].  """

cost = solver.Objective()

for c in customers:
    for p in products: 
        for f in factories:
            if products_from_factories_to_customers[(f,p,c)] is not None:

                cost.SetCoefficient(products_from_factories_to_customers[(f,p,c)], int(Production_cost.loc[p,f]) + int(Shipping_costs.loc[f,c]))


""" PART  H - Define and implement the objective function. Make sure to consider the supplier bills comprising shipping and material costs [2 points] """
for key, value in supplier_sent_material_to_fact.items():
    supplier = key[0]
    material = key[1]
    factory =  key[2]
    
    if value is not None:
        cost.SetCoefficient(value,
                            int(Rawmaterial_costs[material][supplier]) +
                            int(Rawmaterial_shipping[factory][supplier]))


# In[10]:


""" PART  I - Solve the linear program and determine the optimal overall cost [1 point].  """

cost.SetMinimization()
status = solver.Solve()
print(status)

if status == 0:   
    print("Status: ",status,"(Success)")                 
else:  
    print("Status: ",status)
    print("Failed to find a optimal solution")


# ## J. Determine for each factory how much material has to be ordered from each individual supplier [1 point]. 

# In[25]:

""" PART  J - Determine for each factory how much material has to be ordered from each individual supplier [1 point].  """


def j_factory_material_orders(supplier_sent_material_to_fact):
    factories = {}
    print("J Material Orders")
    for key, value in supplier_sent_material_to_fact.items():
        supplier = key[0]
        material = key[1]
        factory = key[2]
        if value is not None:
            if factory not in factories:
                factories[factory] = {}
            if supplier not in factories[factory]:
                factories[factory][supplier] = {}
                factories[factory][supplier]['total'] = 0
            if material not in factories[factory][supplier]:
                factories[factory][supplier][material] = {}
            factories[factory][supplier][material]['volume'] = value.solution_value()
            factories[factory][supplier][material]['cost'] = value.solution_value()* (Rawmaterial_costs[material][supplier] + Rawmaterial_shipping[factory][supplier])
            factories[factory][supplier]['total'] += factories[factory][supplier][material]['cost']
    return factories
j_factory_material_orders =j_factory_material_orders(supplier_sent_material_to_fact)

# print(j_factory_material_orders)


# In[12]:
print("\n\n")
print( "PART  J - Determine for each factory how much material has to be ordered from each individual supplier [1 point].")
for f in j_factory_material_orders.keys():
    print("\n\n")
    print("--"*2,f,"  "*5,"Volume","  "*2,"Cost")
    print(" "*33,"(with shipping)")
    for s in j_factory_material_orders[f].keys():
        print("--"*4,s)
        print()
        for m in j_factory_material_orders[f][s].keys():
            if m in materials:
                print("--"*6,m,"--"*2,int(j_factory_material_orders[f][s][m]["volume"]),"--"*2,int(j_factory_material_orders[f][s][m]["cost"]))


# ## K. Determine for each factory what the supplier bill comprising material cost and delivery will be for each supplier [1 point].

# In[13]:


""" PART  K - Determine for each factory what the supplier bill comprising material cost and delivery will be for each supplier [1 point]. """
print("\n\n")
print(" PART  K - Determine for each factory what the supplier bill comprising material cost and delivery will be for each supplier [1 point]. ")
material_cost_per_factory_wt_shipping = {}
for f in j_factory_material_orders.keys():
    if f not in material_cost_per_factory_wt_shipping.keys():
        material_cost_per_factory_wt_shipping[f] = 0
    print("\n\n")
    print("--"*2,f)
    
    for s in j_factory_material_orders[f].keys():
        material_cost_per_factory_wt_shipping[f] += int(j_factory_material_orders[f][s]["total"])
        print("--"*4,s,"  "*4,"Total Bill",int(j_factory_material_orders[f][s]["total"]))
        
material_cost_per_factory_wt_shipping               


# ## L. Determine for each factory how many units of each product are being manufactured [1 point]. Also determine the total manufacturing cost for each individual factory [1 point]. 
# 
# 

# In[14]:


""" PART  L - Determine for each factory how many units of each product are being manufactured [1 point]  """
print("\n\n")
print(" PART  L - Determine for each factory how many units of each product are being manufactured [1 point]  ")
def l_factory_material_orders(products_from_factories_to_customers):
    factories = {}
    print("l_factory_material_orders")
    for key, value in products_from_factories_to_customers.items():
        factory = key[0]
        product = key[1]
        customer= key[2]
        if factory not in factories.keys():
            factories[factory]={}
        if product not in factories[factory].keys():
            factories[factory][product]=0
        if value is not None:
            factories[factory][product]+=int(value.solution_value())
                                             
    for factory, products in factories.items():
        for product,vol in products.items():
            
        
            print("--"*6,factory,"--"*2,product,"--"*2,"Volume Manufactured===>",vol)
        print("\n\n")
    return factories

l_factory_material_orders = l_factory_material_orders(products_from_factories_to_customers)
# print("l_factory_material_orders")
# print(l_factory_material_orders)
 


# In[15]:


""" PART  L - Also determine the total manufacturing cost for each individual factory [1 point].   """
print("\n\n")
print(" PART  L - Also determine the total manufacturing cost for each individual factory [1 point].   ")

production_cost_per_factory = {}
for f,dic in l_factory_material_orders.items():
    if f  not in production_cost_per_factory.keys():
        production_cost_per_factory[f] = 0
    
    
    for product , vol in dic.items():
        if not pd.isna(Production_cost.loc[product,f]):
            production_cost_per_factory[f] += int(vol) * int(Production_cost.loc[product,f])
# production_cost_per_factory 

for f in production_cost_per_factory.keys():
    print("Total Manufacturing Cost for ",f," is ",production_cost_per_factory[f]+material_cost_per_factory_wt_shipping[f])




# In[16]:


""" PART  M - Determine for each customer how many units of each product are being shipped from each factory [1 point]  """
print("\n\n")
print(" PART  M - Determine for each customer how many units of each product are being shipped from each factory [1 point]  ")
def m_factory_material_orders(products_from_factories_to_customers):
    factories = {}
    # print("m_factory_material_orders")
    for key, value in products_from_factories_to_customers.items():
        if value is not None:
            if int(value.solution_value()) != 0:
                factory = key[0]
                product = key[1]
                customer= key[2]
                if customer not in factories.keys():
                    factories[customer]={}
                if factory not in factories[customer].keys():
                    factories[customer][factory]={}
                if product not in factories[customer][factory].keys():
                    factories[customer][factory][product]=0
                if value is not None:
                    factories[customer][factory][product]+=int(value.solution_value())

    for customer, dic in factories.items():
        for factory,dic2 in dic.items():
            for product,vol in dic2.items():
                print("--"*6,customer,"--"*2,factory,"--"*2,product,"--"*2,"Volume Shipped===>",vol)
        print("\n\n")
    
    return factories
m_factory_material_orders =  m_factory_material_orders(products_from_factories_to_customers)

# print(m_factory_material_orders)


# ##  Also determine the total shipping cost per customer [1 point] 

# In[17]:


""" PART  M -  Also determine the total shipping cost per customer [1 point]  """
print("\n\n")
print(" PART  M -  Also determine the total shipping cost per customer [1 point]  ")
total_shipping_cost_per_customer = {}


for c,dic in m_factory_material_orders.items():
    if c  not in total_shipping_cost_per_customer.keys():
        total_shipping_cost_per_customer[c] = 0
    
    
    for f , dic2 in dic.items():
        if not pd.isna(Shipping_costs.loc[f,c]):
            total_shipping_cost_per_customer[c] += int(Shipping_costs.loc[f,c])
            
print(total_shipping_cost_per_customer)  



# ## N. Determine for each customer the fraction of each material each factory has to order for manufacturing products delivered to that particular customer [1 point].

# In[18]:

""" PART  N - Determine for each customer the fraction of each material each factory has to order for manufacturing products 
              delivered to that particular customer [1 point]."""
print("\n\n")
print(" PART  N - Determine for each customer the fraction of each material each factory has to order for manufacturing products delivered to that particular customer [1 point].")

""" Each factory will source raw material at a a=different cost, find cost of each material for each factory """
per_factory_per_material_cost_and_volume = {}
for factory, dic in j_factory_material_orders.items():
    if not factory in per_factory_per_material_cost_and_volume.keys():
        per_factory_per_material_cost_and_volume[factory] = {}
    
    for supplier , dic2 in dic.items():
        
        for material,volandcost in dic2.items():
            if material in materials:
                if not material in per_factory_per_material_cost_and_volume[factory].keys():
                    per_factory_per_material_cost_and_volume[factory][material] = {}
                    per_factory_per_material_cost_and_volume[factory][material]["cost"] = 0
                    per_factory_per_material_cost_and_volume[factory][material]["volume"] = 0
                per_factory_per_material_cost_and_volume[factory][material]["cost"] +=  int(j_factory_material_orders[factory][supplier][material]["cost"])
                per_factory_per_material_cost_and_volume[factory][material]["volume"] +=  int(j_factory_material_orders[factory][supplier][material]["volume"]   )
per_factory_per_material_cost_and_volume


# In[19]:
""" PART  N - Determine the overall cost of each product per customer including everything [2 point]."""

per_fac_per_prod_productionCost_andVol ={}
for key, value in products_from_factories_to_customers.items():
    if value is not None:
        if int(value.solution_value()) != 0:
            factory = key[0]
            product = key[1]
            customer= key[2]
            if not factory in per_fac_per_prod_productionCost_andVol.keys():
                per_fac_per_prod_productionCost_andVol[factory] = {}
            if not product in per_fac_per_prod_productionCost_andVol[factory].keys():
                per_fac_per_prod_productionCost_andVol[factory][product] = {}
                per_fac_per_prod_productionCost_andVol[factory][product]["cost"] = 0
                per_fac_per_prod_productionCost_andVol[factory][product]["volume"] = 0

            per_fac_per_prod_productionCost_andVol[factory][product]["volume"] += int(value.solution_value())
            per_fac_per_prod_productionCost_andVol[factory][product]["cost"] += int(value.solution_value()) * int(Production_cost.loc[product,factory])

per_fac_per_prod_productionCost_andVol
# In[20]:
per_factory_cost_per_unitOfProduct = {}
for factory, dic in per_fac_per_prod_productionCost_andVol.items():
    if not factory in per_factory_cost_per_unitOfProduct.keys():
        per_factory_cost_per_unitOfProduct[factory]={}
    for product, costandvolume in dic.items():
        if not product in per_factory_cost_per_unitOfProduct[factory].keys():
            per_factory_cost_per_unitOfProduct[factory][product]=0
        c= int(per_fac_per_prod_productionCost_andVol[factory][product]["cost"])
        v= int(per_fac_per_prod_productionCost_andVol[factory][product]["volume"])
        per_factory_cost_per_unitOfProduct[factory][product] += c/v
        
        
        for material in materials:
            cost_per_material = per_factory_per_material_cost_and_volume[factory][material]["cost"]/ per_factory_per_material_cost_and_volume[factory][material]["volume"]
            vol_of_prod_manufactured = per_fac_per_prod_productionCost_andVol[factory][product]["volume"]
            if not pd.isna(Product_requirements.loc[product, material]):
                fraction_of_Material_reqd = Product_requirements.loc[product, material]
                total_cost_ofgiven_material = fraction_of_Material_reqd * cost_per_material 
                per_factory_cost_per_unitOfProduct[factory][product]+= int(total_cost_ofgiven_material)
per_factory_cost_per_unitOfProduct        
        


# In[21]:


def n_factory_material_orders(products_from_factories_to_customers):
    factories = {}
    # print("n_factory_material_orders")
    for key, value in products_from_factories_to_customers.items():
        if value is not None:
            if int(value.solution_value()) != 0:
                factory = key[0]
                product = key[1]
                customer= key[2]
                if customer not in factories.keys():
                    factories[customer]={}
                if product not in factories[customer].keys():
                    factories[customer][product]={}
                if factory not in factories[customer][product].keys():
                    factories[customer][product][factory]={}
                    factories[customer][product][factory]["volume"]=0
                    factories[customer][product][factory]["cost"]=0
                if value is not None:
                    factories[customer][product][factory]["volume"]=int(value.solution_value())
                    shipping_cost = Shipping_costs.loc[factory,customer] * factories[customer][product][factory]["volume"]
                    total_cost = shipping_cost + (factories[customer][product][factory]["volume"] * per_factory_cost_per_unitOfProduct[factory][product])
                    factories[customer][product][factory]["cost"]=int(total_cost)
    for customer, dic in factories.items():
        for product,dic2 in dic.items():
            for factory,volandcost in dic2.items():
            
                
                    
                print("--"*6,customer,"--"*2,product,"--"*2,factory,"--"*2,"Volume Ordered===>",volandcost["volume"],"  Total Bill:",volandcost["cost"])
        print("\n\n")
    
    return factories

total_bill_perCustomer_perProd_perFactory = n_factory_material_orders(products_from_factories_to_customers)


# ##  unit cost of each product per customer 

# In[22]:


unit_cost_of_each_product_per_customer ={}
   
for customer, dic in total_bill_perCustomer_perProd_perFactory.items():
   if not customer in unit_cost_of_each_product_per_customer.keys():
       unit_cost_of_each_product_per_customer[customer]={}
   for product, factorydic in dic.items():
       if not product in unit_cost_of_each_product_per_customer[customer].keys():
           unit_cost_of_each_product_per_customer[customer][product]={}
           unit_cost_of_each_product_per_customer[customer][product]["total cost"] =0
           unit_cost_of_each_product_per_customer[customer][product]["volume"] =0
           unit_cost_of_each_product_per_customer[customer][product]["cost per unit"] = 0

       for factory, costandvolume in factorydic.items():
           
           c= int(total_bill_perCustomer_perProd_perFactory[customer][product][factory]["cost"])
           v= int(total_bill_perCustomer_perProd_perFactory[customer][product][factory]["volume"])
           unit_cost_of_each_product_per_customer[customer][product]["total cost"] += c
           unit_cost_of_each_product_per_customer[customer][product]["volume"] += v
           unit_cost_of_each_product_per_customer[customer][product]["cost per unit"] = int(unit_cost_of_each_product_per_customer[customer][product]["total cost"] / unit_cost_of_each_product_per_customer[customer][product]["volume"])
print("\n\n")
print(" PART  N - Determine the overall cost of each product per customer including everything [2 point].")
# print(unit_cost_of_each_product_per_customer)     
for customer, dic in unit_cost_of_each_product_per_customer.items():
        for product,dic2 in dic.items():
                      
                
                    
            print("--"*6,customer,"--"*2,product,"--"*2,"Total Cost: ",dic2["total cost"],"--"*2,"Volume: ",dic2["volume"], "--"*2, "Cost per Unit:",dic2["cost per unit"])
        print("\n\n")

# In[23]:


# {'Customer A': {'Product A': { 'total cost': 6370,'volume': 7, 'cost per unit': 910},
#                 'Product D': {'total cost': 3941, 'volume': 1, 'cost per unit': 3941}},
 
#  'Customer B': {'Product A': {'total cost': 2292, 'volume': 3, 'cost per unit': 764}},
 
#  'Customer C': {'Product B': {'total cost': 880,  'volume': 1, 'cost per unit': 880},
#                 'Product D': {'total cost': 12093,'volume': 3, 'cost per unit': 4031}},
 
#  'Customer D': {'Product D': {'total cost': 11059,'volume': 4, 'cost per unit': 2764},
#                 'Product C': {'total cost': 11924,'volume': 4, 'cost per unit': 2981}}}


#  ## the cost of manufacturing for the specific customer and all relevant shipping costs 

# In[24]:
print("\n\n")
print(" PART  N - OverAll Bill per Customer.")

cost_of_manufacturing_for_the_specific_customer = {}

for customer, dic in total_bill_perCustomer_perProd_perFactory.items():
    if not customer in cost_of_manufacturing_for_the_specific_customer.keys():
        cost_of_manufacturing_for_the_specific_customer[customer]=0
    for product, factorydic in dic.items():    
        for factory, dic2 in factorydic.items():
            vol= total_bill_perCustomer_perProd_perFactory[customer][product][factory]["volume"] 
            per_manu_cost = int(per_factory_cost_per_unitOfProduct[factory][product])   
            cost_of_manufacturing_for_the_specific_customer[customer]+=(  int(vol) * per_manu_cost )
    
print(cost_of_manufacturing_for_the_specific_customer)

# In[ ]:





# In[ ]:




