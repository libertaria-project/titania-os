<template>
  <div>
    <sidebarParent></sidebarParent>
    <headerParent :name-prop="page"></headerParent>
    <pageLoader v-if="this.$store.state.dockeroverview.length === 0"></pageLoader>
    <div class="margin-20 text-align" v-if="this.$store.state.dockeroverview.length !== 0">
      <div class='col-12'>
      <div class="display-inline-flex dapps-console">
        <div class='float-right display-inline-flex'>
          <div class="label-wrapper">STATUS</div>
          <div class="float-right state-picker" @click="showDropdown()">{{curentState}} <span class='float-right'>&#9662;</span>
             <ul class='dropdown' v-bind:class="{hide: !dropdown}" >
               <li class="float-left col-12 selected" @click="setDropdown('All')">
                 <span class="float-left cursor-pointer overflow-hidden" style="width: 100%;">All</span>
               </li>
               <li class="header-right-options cursor-pointer float-left col-12" @click="setDropdown('Running')">
                 <span title="" class="float-left cursor-pointer overflow-hidden" style="width: 100%;">Running</span>
                 <span style="display: none;"></span>
                 </li>
              <li class="header-right-options cursor-pointer float-left col-12" @click="setDropdown('Paused')">
                <span title="" class="float-left cursor-pointer overflow-hidden" style="width: 100%;">Paused</span>
                <span style="display: none;"></span></li>
              <li class="header-right-options cursor-pointer float-left col-12" @click="setDropdown('Exited')">
                <span title="" class="float-left cursor-pointer overflow-hidden" style="width: 100%;">Exited</span>
                <span style="display: none;"></span></li>
            </ul>
       </div>
        </div>
        <div class="label-wrapper refresh-marker">Refresh every</div>
        <div class='display-inline-flex padding-left-4 refresh-marker'>
        <input type="number" class="col-2 refresh-marker outline-none refresh-field sans-serif-normal small-fontsize" value="1">
        <div class="label-text refresh-marker outline-none sans-serif-normal regular-fontsize">Second(s)</div>
        
      </div>
      <div class='details' @click="getDetails()">{{details}}</div>
      </div>
      </div>
      <div class='general-wrapper-table'>
        <dappsMainContent :state-prop="curentState" :detail-prop="details"></dappsMainContent>
      </div>
    </div>
  </div>
</template>

<script>
import sidebarParent from '@/components/common/sidebarParent'
import headerParent from '@/components/common/headerParent'
import dappsMainContent from '@/components/dappsconsole/dappsMainContent'
import pageLoader from '@/components/common/pageLoader'

export default {
  name: 'dappsconsole',
  computed: {
    page () {
      return 'DAPPS CONSOLE'
    },
    curentState: {
      get: function () {
        return this.$store.state.dappsfilter
      },
      set: function (newfilter) {
        this.$store.state.dappsfilter = newfilter
      }
    },
    details: {
      get: function () {
        return this.$store.state.showDetails
      },
      set: function (newdetails) {
        this.$store.state.showDetails = newdetails
      }
    },
    dropdown: {
      get: function () {
        return this.$store.state.dropdownstate
      },
      set: function (newfilter) {
        this.$store.state.dropdownstate = newfilter
      }
    }
  },
  components: {
    sidebarParent,
    headerParent,
    dappsMainContent,
    pageLoader
  },
  mounted: function () {
    if (this.$route.params.setSession) {
      this.$session.start()
      this.$store.dispatch('getDockerOverview')
      this.$store.state.currentPage = 'dappsconsole'
    } else if (!this.$session.exists()) {
      this.$router.push('/login')
      this.$store.state.currentPage = 'login'
    } else {
      this.$store.dispatch('getDockerOverview')
      this.$store.state.currentPage = 'dappsconsole'
    }
    if (this.$route.params.stopped) {
      this.curentState = 'Exited'
    } else {
      this.curentState = 'All'
    }
  },
  methods: {
    getDetails () {
      if (this.details === 'Hide details') {
        this.details = 'Show details'
      } else {
        this.details = 'Hide details'
      }
    },
    showDropdown () {
      this.dropdown = !this.dropdown
    },
    setDropdown (newdropdown) {
      // this.showDropdown()
      this.curentState = newdropdown
    }
  }
}
</script>
