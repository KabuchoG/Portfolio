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
            <h1>Poem</h1>
          </div>
        </div>
      </div>
    </template>

    <template v-slot:main>
      <div class="user-poem">
        <div>
          <div v-show="isLoadingPoem" class="loading-pane">
            <LoadingIcon/>
          </div>

          <div v-show="poemLoadingFailed">
            <Error404View/>
          </div>

          <div v-show="poemLoaded">
            <Poem :poem="poem" v-for="poem in poems" :key="poem.id"/>
          </div>
          <div
            class="poem-comment-sect-divider"
            v-show="poemLoaded"
          ></div>
          <div v-show="poemLoaded">
            <ItemsLoaderLayout
              :itemsName="'comments'"
              :itemsFetcher="commentsFetcher"
              :reverse="true"
            />
          </div>
        </div>
      </div>
    </template>
  </MainLayout>
</template>

<script lang="ts">
import { Component, Vue } from 'vue-property-decorator';
import { Page, Item } from '@/assets/scripts/types/interfaces';
import CommentAPIReq from '@/assets/scripts/api_requests/comment';
import PoemAPIReq from '@/assets/scripts/api_requests/poem';
import PoemT from '@/assets/scripts/types/poem';
import ArrowLeftIcon from '@/assets/icons/ArrowLeft.vue';
import LoadingIcon from '@/assets/icons/Loading.vue';
import MainLayout from '@/views/layout/Main.vue';
import ItemsLoaderLayout from '@/views/layout/ItemsLoader.vue';
import Error404View from '@/views/error/_Error404.vue';
import Poem from '@/components/Poem.vue';

@Component({
  name: 'PoemView',
  components: {
    ArrowLeftIcon,
    LoadingIcon,
    MainLayout,
    ItemsLoaderLayout,
    Error404View,
    Poem,
  },
})
export default class PoemView extends Vue {
  poems: Array<PoemT> = [];

  poemLoaded = false;

  isLoadingPoem = true;

  poemLoadingFailed = false;

  commentsSrc = '';

  commentsQueryParams = '';

  commentAPIReq = new CommentAPIReq(
    this.$store.state.API_URL,
    this.$store.state.user.authToken,
  );

  poemAPIReq = new PoemAPIReq(
    this.$store.state.API_URL,
    this.$store.state.user.authToken,
  );

  commentsFetcher(page: Page): Promise<{
      success: boolean,
      data?: Array<Item>,
      message?: string
    }> {
    return this.commentAPIReq.getPoemComments(this.$route.params.id, page);
  }

  loadPoem(): void {
    this.poemLoaded = false;
    this.isLoadingPoem = true;
    this.poemLoadingFailed = false;
    this.poemAPIReq.getPoem(this.$route.params.id)
      .then((res) => {
        if (res.success) {
          if (res.data) {
            const n = this.poems.length;
            for (let i = 0; i < n; i += 1) {
              this.poems.pop();
            }
            this.poems.push(res.data);
            document.title = `${res.data.user.name}: ${res.data.title} - Cartedepoezii`;
            this.poemLoaded = true;
          }
        } else {
          document.title = 'Poem Not Found - Cartedepoezii';
          this.poemLoadingFailed = true;
        }
        this.isLoadingPoem = false;
      });
  }

  mounted(): void {
    this.loadPoem();
  }
}
</script>

<style lang="scss">
@use '@/assets/styles/views/poem';
</style>
