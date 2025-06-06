from django.shortcuts import render
from django.http import JsonResponse
from api.models import User, Todo,ChatMessage,Profile

from api.serializer import MyTokenObtainPairSerializer, RegisterSerializer, TodoSerializer,MessageSerializer,ProfileSerializer,UserSerializer
from django.db.models import Subquery,OuterRef,Q
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer


# Get All Routes

@api_view(['GET'])
def getRoutes(request):
    routes = [
        '/api/token/',
        '/api/register/',
        '/api/token/refresh/'
    ]
    return Response(routes)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def testEndPoint(request):
    if request.method == 'GET':
        data = f"Congratulation {request.user}, your API just responded to GET request"
        return Response({'response': data}, status=status.HTTP_200_OK)
    elif request.method == 'POST':
        text = "Hello buddy"
        data = f'Congratulation your API just responded to POST request with text: {text}'
        return Response({'response': data}, status=status.HTTP_200_OK)
    return Response({}, status.HTTP_400_BAD_REQUEST)


class TodoListView(generics.ListCreateAPIView):
    queryset = Todo.objects.all()
    serializer_class = TodoSerializer
    permission_classes=[IsAuthenticated]


    def get_queryset(self):
        user_id = self.kwargs['user_id']
        user = User.objects.get(id=user_id)

        todo = Todo.objects.filter(user=user) 
        return todo
    

class TodoDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TodoSerializer
    permission_classes=[IsAuthenticated]


    def get_object(self):
        user_id = self.kwargs['user_id']
        todo_id = self.kwargs['todo_id']

        user = User.objects.get(id=user_id)
        todo = Todo.objects.get(id=todo_id, user=user)

        return todo
    

class TodoMarkAsCompleted(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TodoSerializer
    permission_classes=[IsAuthenticated]


    def get_object(self):
        user_id = self.kwargs['user_id']
        todo_id = self.kwargs['todo_id']

        user = User.objects.get(id=user_id)
        todo = Todo.objects.get(id=todo_id, user=user)

        todo.completed = True
        todo.save()

        return todo


class MyInbox(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes=[IsAuthenticated]


    def get_queryset(self):
        user_id = self.kwargs['user_id']
        messages = ChatMessage.objects.filter(
            id__in=Subquery(
                User.objects.filter(
                    Q(sender__receiver=user_id) |
                    Q(receiver__sender=user_id)
                ).distinct().annotate(
                    last_meg=Subquery(
                        ChatMessage.objects.filter(
                            Q(sender=OuterRef('id'),receiver=user_id) |
                            Q(receiver=OuterRef('id'),sender=user_id)
                        ).order_by('-id')[:1].values_list('id', flat=True)
                    )
                ).values_list('last_meg', flat=True).order_by('-id')
            )
        ).order_by('-id')
        return messages


from rest_framework.exceptions import ValidationError


class GetMessages(generics.ListAPIView):
    serializer_class = MessageSerializer

    def get_queryset(self):
        sender_id = self.kwargs['sender_id']
        receiver_id = self.kwargs['receiver_id']

        # Get all messages between these two users, regardless of who sent/received
        messages = ChatMessage.objects.filter(
            Q(sender_id=sender_id, receiver_id=receiver_id) |
            Q(sender_id=receiver_id, receiver_id=sender_id)
        ).order_by('date')
        
        return messages

    

class SendMessages(generics.CreateAPIView):
    serializer_class =MessageSerializer



class ProfileDetails(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    queryset = Profile.objects.all()
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)




class SearchUser(generics.ListAPIView):
    serializer_class=ProfileSerializer
    queryset=Profile.objects.all()
    # permission_classes=[IsAuthenticated]

    def list(self, request, *args, **kwargs):
        username=self.kwargs['username']
        logged_in_user=self.request.user
        users=Profile.objects.filter(Q(user__username__icontains=username)|
                                    Q(full_name__icontains=username)|
                                    Q(user__email__icontains=username)
                                    )
        if not users.exists():
            return Response(
                {"detail":"No user founds"},
                status= status.HTTP_404_NOT_FOUND

            )
        serializer=self.get_serializer(users,many=True)
        return Response(serializer.data)





        

    
# views.py এর নিচে যুক্ত করো
class AllUserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    # permission_classes = [IsAuthenticated]
