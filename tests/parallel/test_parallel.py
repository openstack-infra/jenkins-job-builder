# Copyright 2014 David Caro
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from testtools import (
    TestCase,
)
from testtools.matchers import (
    Equals,
    LessThan,
)
from jenkins_jobs.parallel import parallelize
import time
from mock import patch
from multiprocessing import cpu_count


class TestCaseParallel(TestCase):
    def test_parallel_correct_order(self):
        expected = list(range(10, 20))

        @parallelize
        def parallel_test(num_base, num_extra):
            return num_base + num_extra

        parallel_args = [{'num_extra': num} for num in range(10)]
        result = parallel_test(10, parallelize=parallel_args)
        self.assertThat(result, Equals(expected))

    def test_parallel_time_less_than_serial(self):

        @parallelize
        def wait(secs):
            time.sleep(secs)

        before = time.time()
        # ten threads to make it as fast as possible
        wait(parallelize=[{'secs': 1} for _ in range(10)], n_workers=10)
        after = time.time()
        self.assertThat(after - before, LessThan(5))

    def test_parallel_single_thread(self):
        expected = list(range(10, 20))

        @parallelize
        def parallel_test(num_base, num_extra):
            return num_base + num_extra

        parallel_args = [{'num_extra': num} for num in range(10)]
        result = parallel_test(10, parallelize=parallel_args, n_workers=1)
        self.assertThat(result, Equals(expected))

    @patch('multiprocessing.cpu_count')
    def test_use_auto_detect_cores(self, mockCpu_count):

        @parallelize
        def parallel_test():
            return True

        mockCpu_count.return_value = cpu_count()
        result = parallel_test(parallelize=[{} for _ in range(10)],
                               n_workers=0)
        self.assertThat(result, Equals([True for _ in range(10)]))
        mockCpu_count.assert_called()
