from categories.models import Category,UserSubscription

class GetSubscription:
    def __init__(self,save,drop,person,action):
            self.save = save
            self.drop = drop
            self.person = person
            self.all = save+drop
            self.action = action
            self.model_instance = {}
            self.roots = []
            self.selected = {}
            self.should_subscribe ={}
   
    #nodes to be selected
    def select(self):
        for slug in self.save:
            self.selected[slug] = True
        for slug in self.drop:
            self.selected[slug] = False

    #gets all the roots in all categories
    def get_roots(self):
        for slug in self.all:
            category = Category.objects.get(slug=slug)
            self.model_instance[slug] = category
            if category.is_root_node():
                self.roots.append(category)
        
    #checks if this node should be subscribed    
    def check(self,node):
        if node.is_leaf_node():
            if self.selected[node.slug]:
                self.should_subscribe[node.slug] = True #if node is leaf and was selected node should be subscribed 
            else:
                self.should_subscribe[node.slug] = False #if node is leaf and was no selected node shouldn't be subscribed
        else:
            children = node.get_children()
            all_selected = True
            for child in children:
                self.check(child)
                if not self.should_subscribe[child.slug]:
                    all_selected = False
            
            self.should_subscribe[node.slug] = False
            if all_selected:
                self.should_subscribe[node.slug] = True #if all children need to be subscribed, subscribe this node instead of children
                for child in children:
                    self.should_subscribe[child.slug] = False #unsubscribe all children nodes
        
    #this function returns which categories to subscribe and unsubscribe
    def get_should_subscribe(self):
        subscribe = []
        unsubscribe = []
        last_subscribed = {}
        #select the nodes to be selected
        self.select()
        
        #get all the roots
        self.get_roots()

        #check for all the roots
        for root in self.roots:
            self.check(root)
        #initially set the last subscribed as false for all the slugs
        for slug in self.all: 
            last_subscribed[slug] = False
        #set last subscribed true for already subscribed
        for subscription in UserSubscription.objects.filter(person=self.person,action = self.action):
            last_subscribed[subscription.category.slug] = True
        
        for slug in self.all:
            if last_subscribed[slug]:
                if not self.should_subscribe[slug]:
                    unsubscribe.append(self.model_instance[slug]) #if not already subscribed bu need to subscribe this time add to subscribe
            else :
                if self.should_subscribe[slug] :
                    subscribe.append(self.model_instance[slug]) # if subscribed last time but not this time unsubscribe
        
        return subscribe,unsubscribe
