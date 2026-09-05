console.log("Hello World!")
let a=34;
let b=56;

const c = 566;
console.log(a+b);
console.log(a-b);
console.log(a*b);
console.log(a/b);

function sum(a,b){
    return a+b;
}

console.log("The sum of 3 and 6 is " + sum(3,6));

document.getElementById("special").style.color = "red";

let btn = document.getElementById("btn");
btn.addEventListener("click", function(){
    alert("Button was clicked!");
});

let scores = [34, 5, 6];
scores[1] = "Krushi";
alert(scores[1]);

let student = {
    name: "Keval",
    age: 19
};
alert(student['name']);