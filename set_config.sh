export localtest_repo=/Users/prezton/Desktop/CodeBase/project3_localtest_public
export solution_path=/Users/prezton/Desktop/CodeBase/TCPSERVER

docker run -v $localtest_repo:/18441_project3/localtest -v $solution_path:/18441_project3/solution --cap-add NET_ADMIN -it --name project3 cmuee18441/project3:m1chip bash

