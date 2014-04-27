<?php
/*
$d1 = array(1,20);
$d2 = array(2,22);

$d = array();
array_push($d, $d1);
array_push($d, $d2);
  $data = array('points' => $d);

  echo json_encode($data);
*/

// Default values (1 point, which is a rollup of 5 seconds)
$p = 1;
$window = 5;

// Get the variables
if( isset($_GET['p']) ) $p = (int)$_GET["p"];

if( isset($_GET['win']) ) $window = (int)$_GET['win'];

// Create connection
$con = mysqli_connect("localhost","pat","asdfghjkl","Twitter");

// Check connection
if (mysqli_connect_errno())
{
	echo "Failed to connect to MySQL: " . mysqli_connect_error();
	die;
}






$result = mysqli_query($con,"SELECT id, sentiment, count FROM sentiment ORDER BY id DESC LIMIT " . (string)($p * $window));
	
$sent = 0;
$count = 0;
$time = 0;
	
$i = 0;

$output = array();

while($row = mysqli_fetch_array($result))
{
	$sent = $sent + (int)$row['sentiment'];
	$count = $count + (int)$row['count'];
	$time = (int)$row['id'];
	
	$i += 1;
	
	if($i % $window == 0)	// finished one of the rollups, so display it
	{
		$ratio = (float)$sent / (float)$count;
		$time = $time * 1000;
		
		$ret = array($time, $ratio);
		array_push($output, $ret);
		
		//echo json_encode($ret);
		
		$sent = 0;
		$count = 0;
		$time = 0;
	}
	  	
}
$a = array_reverse($output);
/*$out = array();
foreach($a as &$item)
{
	array_push($out, $item[0]);
	array_push($out, $item[1]);
}

echo json_encode($out);*/

if (count($a) == 1)
	echo json_encode($a[0]);
else echo json_encode($a);






// Close MySQL Connection
mysqli_close($con);
?>

