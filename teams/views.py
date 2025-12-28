"""
API views for Team management.

This module contains views for team CRUD operations and team member management.
"""

from rest_framework import status, generics, permissions, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from .models import Team, TeamMember
from .serializers import (
    TeamSerializer,
    TeamMemberSerializer,
    TeamMemberAddSerializer,
    TeamMemberUpdateSerializer,
)
from core.permissions import IsTeamMember

User = get_user_model()


@extend_schema_view(
    get=extend_schema(
        tags=['Teams'],
        summary='List teams',
        description="""
        List all teams that the current user is a member of.
        
        Returns paginated list of teams with their members and details.
        Supports search and ordering.
        
        **Query Parameters:**
        - `search`: Search teams by name or description
        - `ordering`: Order by field (e.g., '-created_at', 'name', 'updated_at')
        - `page`: Page number for pagination (default: 1)
        - `page_size`: Number of items per page (default: 20)
        
        **Authentication:** Required (JWT Bearer token)
        """,
        parameters=[
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search teams by name or description',
            ),
            OpenApiParameter(
                name='ordering',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Order by field (e.g., -created_at, name)',
            ),
        ],
        responses={200: TeamSerializer(many=True)},
    ),
    post=extend_schema(
        tags=['Teams'],
        summary='Create a new team',
        description="""
        Create a new team. The creator automatically becomes the team owner.
        
        **Authentication:** Required (JWT Bearer token)
        **Permissions:** Any authenticated user can create teams
        """,
        request=TeamSerializer,
        responses={
            201: {
                'description': 'Team created successfully',
                'examples': [
                    OpenApiExample(
                        'Success Response',
                        value={
                            'data': {
                                'id': 1,
                                'name': 'Development Team',
                                'description': 'Team responsible for product development',
                                'member_count': 1,
                                'created_at': '2025-12-27T15:00:00Z',
                            },
                            'message': 'Team created successfully',
                        },
                    ),
                ],
            },
            400: {'description': 'Validation error'},
        },
        examples=[
            OpenApiExample(
                'Create Team Request',
                value={
                    'name': 'Development Team',
                    'description': 'Team responsible for product development',
                },
            ),
        ],
    ),
)
class TeamListCreateView(generics.ListCreateAPIView):
    """
    API endpoint for listing and creating teams.
    
    GET /api/teams/ - List teams user is a member of
    POST /api/teams/ - Create a new team
    """
    
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['-created_at']  # Default ordering
    
    def get_queryset(self):
        """
        Return teams that the current user is a member of.
        
        Returns:
            QuerySet: Teams where the current user is a member
        """
        user = self.request.user
        # Get teams where user is a member
        team_ids = TeamMember.objects.filter(user=user).values_list('team_id', flat=True)
        queryset = Team.objects.filter(id__in=team_ids).prefetch_related('members__user')
        return queryset
    
    def perform_create(self, serializer):
        """
        Create a team and automatically add the creator as owner.
        
        Args:
            serializer: TeamSerializer instance with validated data
        """
        team = serializer.save()
        # Automatically add creator as owner
        TeamMember.objects.create(
            team=team,
            user=self.request.user,
            role=TeamMember.ROLE_OWNER
        )
    
    def create(self, request, *args, **kwargs):
        """
        Create a new team and return response with success message.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: JSON response with created team data
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Get the created team with members
        team = serializer.instance
        response_serializer = self.get_serializer(team)
        
        return Response(
            {
                'data': response_serializer.data,
                'message': 'Team created successfully'
            },
            status=status.HTTP_201_CREATED
        )


@extend_schema_view(
    get=extend_schema(
        tags=['Teams'],
        summary='Get team details',
        description='Retrieve detailed information about a specific team including all members.',
        responses={200: TeamSerializer, 404: {'description': 'Team not found'}},
    ),
    put=extend_schema(
        tags=['Teams'],
        summary='Update team (full)',
        description='Full update of team information. All fields must be provided. Requires admin or owner role.',
        request=TeamSerializer,
        responses={
            200: TeamSerializer,
            403: {'description': 'Insufficient permissions'},
            404: {'description': 'Team not found'},
        },
    ),
    patch=extend_schema(
        tags=['Teams'],
        summary='Update team (partial)',
        description='Partial update of team information. Only provided fields will be updated. Requires admin or owner role.',
        request=TeamSerializer,
        responses={
            200: TeamSerializer,
            403: {'description': 'Insufficient permissions'},
            404: {'description': 'Team not found'},
        },
    ),
    delete=extend_schema(
        tags=['Teams'],
        summary='Delete team',
        description='Delete a team. Only team owners can delete teams. This action cannot be undone.',
        responses={
            204: {'description': 'Team deleted successfully'},
            403: {'description': 'Only team owners can delete teams'},
            404: {'description': 'Team not found'},
        },
    ),
)
class TeamDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for retrieving, updating, and deleting a team.
    
    GET /api/teams/{id}/ - Get team details
    PUT /api/teams/{id}/ - Full update (requires admin/owner)
    PATCH /api/teams/{id}/ - Partial update (requires admin/owner)
    DELETE /api/teams/{id}/ - Delete team (requires owner)
    """
    
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeamMember]
    
    def get_queryset(self):
        """
        Return teams that the current user is a member of.
        
        Returns:
            QuerySet: Teams where the current user is a member
        """
        user = self.request.user
        team_ids = TeamMember.objects.filter(user=user).values_list('team_id', flat=True)
        queryset = Team.objects.filter(id__in=team_ids).prefetch_related('members__user')
        return queryset
    
    def get_object(self):
        """
        Get the team object and check permissions.
        
        Returns:
            Team: Team instance
            
        Raises:
            Http404: If team doesn't exist or user is not a member
        """
        team = super().get_object()
        return team
    
    def update(self, request, *args, **kwargs):
        """
        Update team information (PUT).
        
        Only team admins and owners can update teams.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: JSON response with updated team data
        """
        team = self.get_object()
        user = request.user
        
        # Check if user is admin or owner
        if not team.is_admin(user):
            return Response(
                {'error': 'Only team admins and owners can update team information.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(team, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(
            {
                'data': serializer.data,
                'message': 'Team updated successfully'
            },
            status=status.HTTP_200_OK
        )
    
    def partial_update(self, request, *args, **kwargs):
        """
        Partially update team information (PATCH).
        
        Only team admins and owners can update teams.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: JSON response with updated team data
        """
        team = self.get_object()
        user = request.user
        
        # Check if user is admin or owner
        if not team.is_admin(user):
            return Response(
                {'error': 'Only team admins and owners can update team information.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(team, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(
            {
                'data': serializer.data,
                'message': 'Team updated successfully'
            },
            status=status.HTTP_200_OK
        )
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete a team (DELETE).
        
        Only team owners can delete teams.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: Empty response with 204 status
        """
        team = self.get_object()
        user = request.user
        
        # Check if user is the owner
        if not team.is_owner(user):
            return Response(
                {'error': 'Only team owners can delete teams.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        team_name = team.name
        self.perform_destroy(team)
        
        return Response(
            {'message': f'Team "{team_name}" deleted successfully'},
            status=status.HTTP_204_NO_CONTENT
        )


@extend_schema_view(
    post=extend_schema(
        tags=['Teams'],
        summary='Add team member',
        description="""
        Add a new member to a team.
        
        **Authentication:** Required (JWT Bearer token)
        **Permissions:** User must be an admin or owner of the team
        
        **Request Body:**
        - `user_id` (required): ID of the user to add to the team
        - `role` (optional): Role to assign (owner, admin, member). Defaults to 'member'
          - Only team owners can assign the 'owner' role
        
        **Validation Rules:**
        - User must exist
        - User cannot already be a member of the team
        - Only team owners can assign the 'owner' role
        
        **Response:**
        Returns the created team member with full details including user information.
        """,
        request=TeamMemberAddSerializer,
        responses={
            201: {
                'description': 'Member added successfully',
                'examples': [
                    OpenApiExample(
                        'Success Response',
                        value={
                            'data': {
                                'id': 1,
                                'user': 2,
                                'username': 'johndoe',
                                'email': 'john@example.com',
                                'full_name': 'John Doe',
                                'role': 'member',
                                'role_display': 'Member',
                                'joined_at': '2025-12-27T15:00:00Z',
                            },
                            'message': 'Member added successfully',
                        },
                    ),
                ],
            },
            400: {
                'description': 'Validation error',
                'examples': [
                    OpenApiExample(
                        'User Already Member',
                        value={'error': 'User is already a member of this team.'},
                    ),
                ],
            },
            403: {
                'description': 'Insufficient permissions',
                'examples': [
                    OpenApiExample(
                        'Not Admin',
                        value={'error': 'Only team admins and owners can add members.'},
                    ),
                ],
            },
            404: {
                'description': 'User or team not found',
            },
        },
        examples=[
            OpenApiExample(
                'Add Member Request',
                value={
                    'user_id': 2,
                    'role': 'member',
                },
            ),
        ],
    ),
    patch=extend_schema(
        tags=['Teams'],
        summary='Update team member role',
        description="""
        Update a member's role in the team.
        
        **Authentication:** Required (JWT Bearer token)
        **Permissions:** User must be an admin or owner of the team
        
        **Request Body:**
        - `role` (required): New role to assign (owner, admin, member)
          - Only team owners can assign the 'owner' role
          - Cannot change the role of the team owner
        
        **Validation Rules:**
        - Member must exist in the team
        - Cannot change the role of the team owner
        - Only team owners can assign the 'owner' role
        
        **Response:**
        Returns the updated team member with new role information.
        """,
        request=TeamMemberUpdateSerializer,
        responses={
            200: {
                'description': 'Member role updated successfully',
                'examples': [
                    OpenApiExample(
                        'Success Response',
                        value={
                            'data': {
                                'id': 1,
                                'user': 2,
                                'username': 'johndoe',
                                'email': 'john@example.com',
                                'full_name': 'John Doe',
                                'role': 'admin',
                                'role_display': 'Admin',
                                'joined_at': '2025-12-27T15:00:00Z',
                            },
                            'message': 'Member role updated successfully',
                        },
                    ),
                ],
            },
            400: {
                'description': 'Validation error',
                'examples': [
                    OpenApiExample(
                        'Cannot Change Owner Role',
                        value={'error': 'Cannot change the role of the team owner.'},
                    ),
                ],
            },
            403: {
                'description': 'Insufficient permissions',
            },
            404: {
                'description': 'Member not found',
            },
        },
        examples=[
            OpenApiExample(
                'Update Role Request',
                value={
                    'role': 'admin',
                },
            ),
        ],
    ),
    delete=extend_schema(
        tags=['Teams'],
        summary='Remove team member',
        description="""
        Remove a member from the team.
        
        **Authentication:** Required (JWT Bearer token)
        **Permissions:** User must be an admin or owner of the team
        
        **Validation Rules:**
        - Member must exist in the team
        - Cannot remove the team owner
        - Cannot remove yourself (contact another admin or owner)
        
        **Response:**
        Returns a success message confirming the member was removed.
        """,
        responses={
            204: {
                'description': 'Member removed successfully',
                'examples': [
                    OpenApiExample(
                        'Success Response',
                        value={'message': 'Member "johndoe" removed from team successfully'},
                    ),
                ],
            },
            400: {
                'description': 'Validation error',
                'examples': [
                    OpenApiExample(
                        'Cannot Remove Owner',
                        value={
                            'error': 'Cannot remove the team owner. Transfer ownership first or delete the team.',
                        },
                    ),
                    OpenApiExample(
                        'Cannot Remove Self',
                        value={
                            'error': 'You cannot remove yourself from the team. Please contact another admin or owner.',
                        },
                    ),
                ],
            },
            403: {
                'description': 'Insufficient permissions',
            },
            404: {
                'description': 'Member not found',
            },
        },
    ),
)
class TeamMemberView(APIView):
    """
    API endpoint for managing team members.
    
    POST /api/teams/{team_id}/members/ - Add a new member to the team
    PATCH /api/teams/{team_id}/members/{user_id}/ - Update a member's role
    DELETE /api/teams/{team_id}/members/{user_id}/ - Remove a member from the team
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_team(self, team_id):
        """
        Get team object and verify user is a member.
        
        Args:
            team_id: Team ID
            
        Returns:
            Team: Team instance
            
        Raises:
            Http404: If team doesn't exist or user is not a member
        """
        user = self.request.user
        team_ids = TeamMember.objects.filter(user=user).values_list('team_id', flat=True)
        team = get_object_or_404(Team.objects.filter(id__in=team_ids), pk=team_id)
        return team
    
    def post(self, request, team_id):
        """
        Add a new member to the team.
        
        Args:
            request: HTTP request object
            team_id: Team ID
            
        Returns:
            Response: JSON response with created member data
        """
        team = self.get_team(team_id)
        user = request.user
        
        # Check if user is admin or owner
        if not team.is_admin(user):
            return Response(
                {'error': 'Only team admins and owners can add members.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = TeamMemberAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_id = serializer.validated_data['user_id']
        role = serializer.validated_data.get('role', TeamMember.ROLE_MEMBER)
        
        # Get the user to add
        try:
            user_to_add = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user is already a member
        if team.is_member(user_to_add):
            return Response(
                {'error': 'User is already a member of this team.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Prevent non-owners from assigning owner role
        if role == TeamMember.ROLE_OWNER and not team.is_owner(user):
            return Response(
                {'error': 'Only team owners can assign owner role.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create team membership
        team_member = TeamMember.objects.create(
            team=team,
            user=user_to_add,
            role=role
        )
        
        # Serialize and return response
        member_serializer = TeamMemberSerializer(team_member)
        
        return Response(
            {
                'data': member_serializer.data,
                'message': 'Member added successfully'
            },
            status=status.HTTP_201_CREATED
        )
    
    def patch(self, request, team_id, user_id):
        """
        Update a member's role in the team.
        
        Args:
            request: HTTP request object
            team_id: Team ID
            user_id: User ID of the member to update
            
        Returns:
            Response: JSON response with updated member data
        """
        team = self.get_team(team_id)
        user = request.user
        
        # Check if user is admin or owner
        if not team.is_admin(user):
            return Response(
                {'error': 'Only team admins and owners can update member roles.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get the team member to update
        try:
            team_member = TeamMember.objects.get(team=team, user_id=user_id)
        except TeamMember.DoesNotExist:
            return Response(
                {'error': 'Member not found in this team.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Cannot change owner role
        if team_member.role == TeamMember.ROLE_OWNER:
            return Response(
                {'error': 'Cannot change the role of the team owner.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = TeamMemberUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        new_role = serializer.validated_data['role']
        
        # Prevent non-owners from assigning owner role
        if new_role == TeamMember.ROLE_OWNER and not team.is_owner(user):
            return Response(
                {'error': 'Only team owners can assign owner role.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update role
        team_member.role = new_role
        team_member.save()
        
        # Serialize and return response
        member_serializer = TeamMemberSerializer(team_member)
        
        return Response(
            {
                'data': member_serializer.data,
                'message': 'Member role updated successfully'
            },
            status=status.HTTP_200_OK
        )
    
    def delete(self, request, team_id, user_id):
        """
        Remove a member from the team.
        
        Args:
            request: HTTP request object
            team_id: Team ID
            user_id: User ID of the member to remove
            
        Returns:
            Response: Empty response with 204 status
        """
        team = self.get_team(team_id)
        user = request.user
        
        # Check if user is admin or owner
        if not team.is_admin(user):
            return Response(
                {'error': 'Only team admins and owners can remove members.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get the team member to remove
        try:
            team_member = TeamMember.objects.get(team=team, user_id=user_id)
        except TeamMember.DoesNotExist:
            return Response(
                {'error': 'Member not found in this team.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Cannot remove team owner
        if team_member.role == TeamMember.ROLE_OWNER:
            return Response(
                {'error': 'Cannot remove the team owner. Transfer ownership first or delete the team.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Cannot remove yourself (use leave team endpoint if needed)
        if team_member.user == user:
            return Response(
                {'error': 'You cannot remove yourself from the team. Please contact another admin or owner.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Remove member
        username = team_member.user.username
        team_member.delete()
        
        return Response(
            {'message': f'Member "{username}" removed from team successfully'},
            status=status.HTTP_204_NO_CONTENT
        )
