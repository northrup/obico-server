<template>
  <div>
    <div>
      <h5>Serial Port:</h5>
    </div>
    <div>
      <b-form-select id="connect-port" v-model="selectedPort">
        <b-form-select-option v-for="port in connectionOptions.ports" :key="port" :value="port">
          {{ port }}
        </b-form-select-option>
      </b-form-select>
    </div>
    <br />
    <div>
      <h5>Baudrate:</h5>
    </div>
    <div>
      <b-form-select id="connect-baudrate" v-model="selectedBaudrate">
        <b-form-select-option value=""> Auto </b-form-select-option>
        <b-form-select-option
          v-for="baudrate in connectionOptions.baudrates"
          :key="baudrate"
          :value="baudrate"
        >
          {{ baudrate }}
        </b-form-select-option>
      </b-form-select>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ConnectPrinter',
  props: {
    connectionOptions: {
      type: Object,
      required: true,
    },
  },

  data() {
    return {
      selectedPort: this.connectionOptions.ports[0],
      selectedBaudrate: '',
    }
  },
}
</script>
