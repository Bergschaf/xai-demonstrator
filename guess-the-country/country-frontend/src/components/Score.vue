<template>
  <div class="wrapper">    
   <section  class="left xd-section xd-light">
        <p>Round: {{round}}/{{nr_of_rounds}}</p>
   </section>   
  </div>
</template>
<script>

export default {
  name: "Score",
props: {
      score_user: {
          type: Number,
      },
    score_ai: {
          type: Number,
      },
      round: {
        type: Number,
      },
 user_city_answer: {
   type: String
 },
  nr_of_rounds: {
        type: Number
  }
}
}
</script>
<style scoped>

.wrapper {
  display: flex;
  flex-direction: row;
  align-items: stretch;
  width: 100%;
  gap:10px;
}

.wrapper>.left {
  text-align: center;
    flex: 4; 
}

.wrapper>.right{
 text-align: center;
 flex: 6;

}

.xd-section:last-child{
    margin-bottom: 12px;
}
</style>
