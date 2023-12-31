<template>
  <MainLayout>
    <template v-slot:header>
      <div class="header-pane">
        <div class="page-nav-bar">
          <div>
            <button class="cdp-btn icon">
              <ArrowLeftIcon/>
            </button>
          </div>
          <div>
            <h2>{{ user.name || 'Profile' }}</h2>
            <h5 class="">{{ getSubTitle() }}</h5>
          </div>
        </div>
      </div>
    </template>

    <template v-slot:main>
      <div class="user-profile">
        <div class="profile-info" v-show="userInfoLoaded">
          <div>
            <div class="profile-photo-sect">
              <button class="image-view-btn">
                <AccountIcon/>
                <img :src="profilePhotoSrc"/>
              </button>

              <button
                :class="{
                  'cdp-btn': true,
                  text: true,
                  light: actionText === 'Follow' || actionText === 'Edit Profile',
                  danger: actionText === 'Unfollow'
                }"
                @click="execAction"
                @mouseenter="onMouseEnterAction"
                @mouseleave="onMouseLeaveAction"
              >
                {{ actionText }}
              </button>
            </div>

            <div class="name-sect">
              {{ user.name }}
            </div>

            <div class="join-sect">
              <CalendarMonthIcon/>
              <span>{{ getJoinDate() }}</span>
            </div>

            <div class="connections-sect">
              <button @click="viewFollowers">
                <b>{{ MathUtils.formatNumber(user.followersCount) }}</b>
                <b>{{ user.followersCount === 1 ? 'Follower' : 'Followers'}}</b>
              </button>
              <button @click="viewFollowings">
                <b>{{ MathUtils.formatNumber(user.followingsCount) }}</b>
                <b>{{ user.followingsCount === 1 ? 'Following' : 'Followings'}}</b>
              </button>
            </div>

            <div class="bio-sect" v-show="user.bio.length > 0">
              {{ user.bio }}
            </div>
          </div>
        </div>

        <div v-show="isLoadingProfile" class="loading-pane">
          <LoadingIcon/>
        </div>

        <div v-show="profileLoadingFailed">
          <Error404View/>
        </div>

        <ModalLayout
          :modalOpen="openDialog"
          :modalTitle="dialogTitle"
          :hasHeader="hasHeader"
          v-on:request-close="closeDialog"
        >
          <template v-slot:modal-body>
            <div>
              <div class="followers" v-show="dialogState === DialogStates.Followers">
                <ItemsLoaderLayout
                  :itemsName="'users'"
                  :itemsFetcher="followersFetcher"
                />
              </div>
              <div class="followings" v-show="dialogState === DialogStates.Followings">
                <ItemsLoaderLayout
                  :itemsName="'users'"
                  :itemsFetcher="followingsFetcher"
                />
              </div>
              <div class="edit-profile" v-show="dialogState === DialogStates.EditProfile">
                <EditProfileView
                  :userProfile="editableProfileInfo"
                  :updateView="updateEditProfile"
                  v-on:image-uploaded="imageUploaded"
                  v-on:image-deleted="imageDeleted"
                />
              </div>
              <!-- <div class="followings" v-show="dialogState === DialogStates.ProfilePhoto">
                <UserItem :user="userTest"/>
              </div> -->
            </div>
          </template>

          <template v-slot:modal-action-panel>
            <div v-show="dialogState === DialogStates.EditProfile">
              <div>
                <button
                  :class="{
                    'cdp-btn': true,
                    'text': !isSavingProfile,
                    'icon': isSavingProfile
                    }"
                    :disabled="isSavingProfile"
                    @click="saveProfile"
                >
                  <LoadingIcon v-show="isSavingProfile"/>
                  <b v-show="!isSavingProfile">Save</b>
                </button>
              </div>
            </div>
          </template>
        </ModalLayout>

        <TabsLayout
          v-show="userInfoLoaded"
          :items="tabItems"
          v-bind:selectedId="selectedId"
          v-on:select-tab="args => changeSelectedTab(args)"
        >
          <div v-show="selectedId === 1">
            <ItemsLoaderLayout
              :itemsName="'poems'"
              :itemsFetcher="poemsFetcher"
              :reverse="true"
              :updateItemView="selectedId === 1"
            />
          </div>
          <div v-show="selectedId === 2">
            <ItemsLoaderLayout
              :itemsName="'comments'"
              :itemsFetcher="commentsFetcher"
              :reverse="true"
              :updateItemView="selectedId === 2"
            />
          </div>
          <div v-show="selectedId === 3">
            <ItemsLoaderLayout
              :itemsName="'poems'"
              :itemsFetcher="likesFetcher"
              :reverse="true"
              :updateItemView="selectedId === 3"
            />
          </div>
        </TabsLayout>
      </div>
    </template>
  </MainLayout>
</template>

<script lang="ts">
import { Component, Vue } from 'vue-property-decorator';
import {
  EditProfileForm,
  Page,
  Item,
} from '@/assets/scripts/types/interfaces';
import User from '@/assets/scripts/types/user';
import MathUtils from '@/assets/scripts/math_utils';
import ConnectionAPIReq from '@/assets/scripts/api_requests/connection';
import UserAPIReq from '@/assets/scripts/api_requests/user';
import PoemAPIReq from '@/assets/scripts/api_requests/poem';
import CommentAPIReq from '@/assets/scripts/api_requests/comment';
import MainLayout from '@/views/layout/Main.vue';
import TabsLayout from '@/views/layout/Tabs.vue';
import ModalLayout from '@/views/layout/Modal.vue';
import ItemsLoaderLayout from '@/views/layout/ItemsLoader.vue';
import EditProfileView from '@/views/settings/EditProfile.vue';
import Error404View from '@/views/error/_Error404.vue';
import Poem from '@/components/Poem.vue';
import Comment from '@/components/Comment.vue';
import UserItem from '@/components/UserItem.vue';
import ArrowLeftIcon from '@/assets/icons/ArrowLeft.vue';
import AccountIcon from '@/assets/icons/Account.vue';
import LoadingIcon from '@/assets/icons/Loading.vue';
import CalendarMonthIcon from '@/assets/icons/CalendarMonth.vue';

@Component({
  name: 'ProfileView',
  components: {
    MainLayout,
    TabsLayout,
    ModalLayout,
    ItemsLoaderLayout,
    EditProfileView,
    Error404View,
    Poem,
    Comment,
    UserItem,
    ArrowLeftIcon,
    AccountIcon,
    LoadingIcon,
    CalendarMonthIcon,
  },
})
export default class ProfileView extends Vue {
  actionText = '';

  hasHeader = true;

  hasFooter = true;

  dialogTitle = '';

  openDialog = false;

  dialogState = 0;

  DialogStates = {
    None: 0,
    Followers: 1,
    Followings: 2,
    EditProfile: 3,
    ProfilePhoto: 4,
  }

  MathUtils = MathUtils;

  tabItems = [
    {
      id: 1,
      title: 'Poems',
    },
    {
      id: 2,
      title: 'Comments',
    },
    {
      id: 3,
      title: 'Likes',
    },
  ];

  selectedId = 0;

  user: User = new User();

  editableProfileInfo: EditProfileForm = {
    userId: '',
    imageId: '',
    imageURL: '',
    imageUploaded: false,
    removePhoto: false,
    email: '',
    name: '',
    bio: '',
  };

  updateEditProfile = false;

  isLoadingProfile = true;

  profileLoadingFailed = false;

  isSavingProfile = false;

  isFollowingUser = false;

  profilePhotoSrc = '';

  userInfoLoaded = false;

  poemAPIReq = new PoemAPIReq(
    this.$store.state.API_URL,
    this.$store.state.user.authToken,
  );

  connectionAPIReq = new ConnectionAPIReq(
    this.$store.state.API_URL,
    this.$store.state.user.authToken,
  );

  userAPIReq = new UserAPIReq(
    this.$store.state.API_URL,
    this.$store.state.user.authToken,
  );

  commentAPIReq = new CommentAPIReq(
    this.$store.state.API_URL,
    this.$store.state.user.authToken,
  );

  loadUserInfo(): void {
    this.userAPIReq.getUser(this.$route.params.id)
      .then((res) => {
        if (res.success) {
          if (res.data) {
            this.user = res.data;
            this.isFollowingUser = this.user.isFollowing;
            this.loadProfilePhoto();
            this.onMouseLeaveAction();
            document.title = `${res.data.name} - Cartedepoezii`;
            this.userInfoLoaded = true;
            this.profileLoadingFailed = false;
          }
        } else {
          console.error(res.message);
          document.title = 'User Not Found - Cartedepoezii';
          this.profileLoadingFailed = true;
        }
        this.isLoadingProfile = false;
      });
  }

  loadProfilePhoto(): void {
    this.userAPIReq.getProfilePhoto(this.user.profilePhotoId)
      .then((res) => {
        if (res.success) {
          if (res.data) {
            this.profilePhotoSrc = `${res.data.url}?tr=w-120,h-120`;
          }
        }
      });
  }

  toggleConnection(): void {
    const userId = this.$store.state.user.id;
    const followId = this.$route.params.id;
    this.isFollowingUser = !this.isFollowingUser;
    this.connectionAPIReq.follow(userId, followId)
      .then((res) => {
        if (res.success) {
          if (res.data) {
            this.isFollowingUser = res.data.status;
            this.onMouseLeaveAction();
          }
        } else {
          console.error(res.message);
        }
        this.userInfoLoaded = true;
      });
  }

  saveProfile(): void {
    this.isSavingProfile = true;
    this.userAPIReq.updateUser(this.editableProfileInfo)
      .then((res) => {
        if (res.success) {
          if (res.data) {
            this.$store.commit('signIn', {
              id: this.user.id,
              token: res.data.authToken,
            });
            this.user.profilePhotoId = res.data.profilePhotoId;
            this.loadProfilePhoto();
          }
        } else {
          console.error(res.message);
        }
        this.isSavingProfile = false;
        this.closeDialog();
      }).catch(() => {
        this.isSavingProfile = false;
        this.closeDialog();
      });
  }

  followersFetcher(page: Page): Promise<{
      success: boolean,
      data?: Array<Item>,
      message?: string
    }> {
    return this.connectionAPIReq.getFollowers(this.$route.params.id, page);
  }

  followingsFetcher(page: Page): Promise<{
      success: boolean,
      data?: Array<Item>,
      message?: string
    }> {
    return this.connectionAPIReq.getFollowings(this.$route.params.id, page);
  }

  poemsFetcher(page: Page): Promise<{
      success: boolean,
      data?: Array<Item>,
      message?: string
    }> {
    return this.poemAPIReq.getPoemsUserCreated(this.$route.params.id, page);
  }

  commentsFetcher(page: Page): Promise<{
      success: boolean,
      data?: Array<Item>,
      message?: string
    }> {
    return this.commentAPIReq.getCommentsByUser(this.$route.params.id, page);
  }

  likesFetcher(page: Page): Promise<{
      success: boolean,
      data?: Array<Item>,
      message?: string
    }> {
    return this.poemAPIReq.getPoemsUserLikes(this.$route.params.id, page);
  }

  getJoinDate(): string {
    if (!this.user) {
      return '';
    }
    const joinDate = new Date(this.user.joined);
    const months = [
      'January',
      'February',
      'March',
      'April',
      'May',
      'June',
      'July',
      'August',
      'September',
      'October',
      'November',
      'December',
    ];
    return `Joined ${months[joinDate.getMonth()]} ${joinDate.getFullYear()}`;
  }

  imageUploaded(imgSrc: string):void {
    this.editableProfileInfo.imageUploaded = true;
    this.editableProfileInfo.imageURL = imgSrc;
  }

  imageDeleted():void {
    this.editableProfileInfo.removePhoto = true;
    this.editableProfileInfo.imageURL = '';
  }

  onMouseEnterAction(): void {
    if (this.user.id === this.$store.state.user.id) {
      this.actionText = 'Edit Profile';
    } else if (this.isFollowingUser) {
      this.actionText = 'Unfollow';
    } else {
      this.actionText = 'Follow';
    }
  }

  onMouseLeaveAction(): void {
    if (!this.user) {
      return;
    }
    if (this.user.id === this.$store.state.user.id) {
      this.actionText = 'Edit Profile';
    } else if (this.isFollowingUser) {
      this.actionText = 'Following';
    } else {
      this.actionText = 'Follow';
    }
  }

  getSubTitle(): string {
    if (!this.user) {
      return '';
    }
    switch (this.selectedId) {
      case 1: {
        const n = MathUtils.formatNumber(this.user.poemsCount, true);
        return this.user.poemsCount === 1 ? `${n} Poem` : `${n} Poems`;
      }
      case 2: {
        const n = MathUtils.formatNumber(this.user.commentsCount, true);
        return this.user.commentsCount === 1 ? `${n} Comment` : `${n} Comments`;
      }
      case 3: {
        const n = MathUtils.formatNumber(this.user.likesCount, true);
        return this.user.likesCount === 1 ? `${n} Like` : `${n} Likes`;
      }
      default:
        return '';
    }
  }

  execAction(): void {
    let actionId = -1;
    if (this.user.id === this.$store.state.user.id) {
      actionId = 0;
    } else if (this.isFollowingUser) {
      actionId = 1;
    } else {
      actionId = 2;
    }
    switch (actionId) {
      case 0: {
        this.viewEditProfile();
        break;
      }
      case 1:
      case 2: {
        this.toggleConnection();
        break;
      }
      default:
        break;
    }
  }

  viewFollowers(): void {
    this.openDialog = true;
    this.dialogTitle = 'Followed by';
    this.hasHeader = true;
    this.hasFooter = false;
    this.dialogState = this.DialogStates.Followers;
  }

  viewFollowings(): void {
    this.openDialog = true;
    this.dialogTitle = 'Following';
    this.hasHeader = true;
    this.hasFooter = false;
    this.dialogState = this.DialogStates.Followings;
  }

  viewEditProfile(): void {
    this.openDialog = true;
    this.dialogTitle = 'Edit Profile';
    this.hasHeader = true;
    this.hasFooter = true;
    this.editableProfileInfo = {
      userId: this.user.id,
      imageId: this.user.profilePhotoId,
      imageURL: this.profilePhotoSrc,
      imageUploaded: false,
      removePhoto: false,
      email: this.user.email || '',
      name: this.user.name,
      bio: this.user.bio,
    };
    this.updateEditProfile = true;
    this.dialogState = this.DialogStates.EditProfile;
  }

  closeDialog(): void {
    this.openDialog = false;
  }

  changeSelectedTab(tabId: number): void {
    this.selectedId = tabId;
  }

  created(): void {
    if (this.user.id === this.$store.state.user.id) {
      this.actionText = 'Edit Profile';
    } else if (this.isFollowingUser) {
      this.actionText = 'Following';
    } else {
      this.actionText = 'Follow';
    }
    this.dialogState = this.DialogStates.None;
  }

  mounted(): void {
    this.loadUserInfo();
  }
}
</script>

<style lang="scss">
@use '@/assets/styles/views/profile';
</style>
