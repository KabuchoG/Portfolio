<template>
  <MainAltLayout>
    <div class="guest-home">
      <div class="main">
        <div>
          <img
            class="bg"
            loading="lazy"
            src="https://ik.imagekit.io/B3zaleel/cartedepoezii/home_background_Rt74hKhSK.jpg?tr=pr-true&ik-sdk-version=javascript-1.4.3&updatedAt=1647505084730"
          />
          <div class="bg">
            <Logo/>
          </div>
        </div>

        <div>
          <div>
            <h2>Join Cartedepoezii today.</h2>
            <router-link class="cdp-btn text" to="/sign-up">Sign up with email</router-link>
            <div>
              <h4>
                By signing up, you agree to our
                <router-link class="alt-link" to="/terms-of-service">Terms of service</router-link>
                and <router-link class="alt-link" to="privacy-policy">Privacy Policy</router-link>.
              </h4>
            </div>
          </div>

          <div>
            <h3>Already have an account?</h3>
            <router-link class="cdp-btn text" to="/sign-in">Sign In</router-link>
          </div>
        </div>
      </div>
    </div>
  </MainAltLayout>
</template>

<script lang="ts">
import { Component, Vue } from 'vue-property-decorator';
import MainAltLayout from '@/views/layout/MainAlt.vue';
import Logo from '@/assets/icons/Logo.vue';

@Component({
  name: 'GuestHomeView',
  components: {
    MainAltLayout,
    Logo,
  },
})
export default class GuestHomeView extends Vue {}
</script>

<style lang="scss">
@use "@/assets/styles/views/guest_home";
</style>
