import * as UTILS from './utils.js';

export class Player {

	// static paddle = Player.loadPaddle();

	constructor(paddle) {
		this.mesh = paddle.clone();
		// console.log(this.mesh)
		this.speed = UTILS.MOVSPEED;
        this.name = "Undefined";
		this.moves = {
			up: false,
			down:false
		}
		this.mesh.position.z = -10;
		this.powerUp = null;
		this.upKey = null;
		this.downKey = null;
	}
}
